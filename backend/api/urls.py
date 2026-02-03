from django.urls import path
from .views import CSVAnalysisView, ExportPDFView

urlpatterns = [
    path('upload/', CSVAnalysisView.as_view(), name='csv-upload'),
    path('analyze/', CSVAnalysisView.as_view(), name='csv-analyze'),
    path('export-pdf/', ExportPDFView.as_view(), name='export-pdf'),
]

