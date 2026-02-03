import pandas as pd
from io import BytesIO
from django.http import HttpResponse
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from rest_framework.authentication import BasicAuthentication
from rest_framework.permissions import IsAuthenticated
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import letter

from .models import EquipmentDataset

class CSVAnalysisView(APIView):
    parser_classes = [MultiPartParser]
    authentication_classes = [BasicAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Fetch the last 5 datasets for History Management."""
        history = EquipmentDataset.objects.all().order_by('-uploaded_at')[:5]
        data = [{
            "id": h.id,
            "file_name": h.file_name,
            "uploaded_at": h.uploaded_at.strftime("%Y-%m-%d %H:%M"),
            "results": h.analysis_results
        } for h in history]
        return Response(data)

    def post(self, request):
        """Parse CSV, perform analysis, and maintain a 5-record history."""
        file_obj = request.data.get('file')
        if not file_obj:
            return Response({"error": "No file provided"}, status=400)

        try:
            df = pd.read_csv(file_obj)
            
            required = {'Temperature', 'Pressure', 'Flowrate', 'Type'}
            if not required.issubset(df.columns):
                return Response({"error": f"Invalid CSV. Missing: {required - set(df.columns)}"}, status=400)

            analysis = {
                "total_count": len(df),
                "averages": {
                    "temp": round(float(df['Temperature'].mean()), 2),
                    "pressure": round(float(df['Pressure'].mean()), 2),
                    "flowrate": round(float(df['Flowrate'].mean()), 2),
                },
                "distribution": df['Type'].value_counts().to_dict()
            }

            with transaction.atomic():
                EquipmentDataset.objects.create(
                    file_name=file_obj.name,
                    analysis_results=analysis
                )

                all_ids = EquipmentDataset.objects.order_by('-uploaded_at').values_list('id', flat=True)
                if len(all_ids) > 5:
                    EquipmentDataset.objects.exclude(id__in=all_ids[:5]).delete()

            return Response(analysis)

        except Exception as e:
            return Response({"error": f"Processing failed: {str(e)}"}, status=400)


class ExportPDFView(APIView):
    """Generates a PDF report from the most recent analysis."""
    authentication_classes = [BasicAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        last_upload = EquipmentDataset.objects.order_by('-uploaded_at').first()
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()

        elements.append(Paragraph("Chemical Equipment Parameter Report", styles['Title']))
        elements.append(Spacer(1, 12))

        if last_upload:
            res = last_upload.analysis_results
            data = [
                ["Metric", "Value"],
                ["File Name", last_upload.file_name],
                ["Total Equipment", res['total_count']],
                ["Average Temp", f"{res['averages']['temp']} °C"],
                ["Average Pressure", f"{res['averages']['pressure']} bar"],
                ["Average Flowrate", f"{res['averages']['flowrate']} L/min"]
            ]

            table = Table(data, colWidths=[150, 250])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.cadetblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
            ]))
            elements.append(table)
        else:
            elements.append(Paragraph("No data available. Please upload a CSV first.", styles['Normal']))

        doc.build(elements)
        
        pdf_content = buffer.getvalue()
        buffer.close()
        
        response = HttpResponse(pdf_content, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="Equipment_Report.pdf"'
        return response