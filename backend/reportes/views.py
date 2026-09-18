from django.http import HttpResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from . import services
from .pdf import ErrorConversionPDF
from .serializers import GenerarReporteSerializer

TIPOS_MIME = {
    "pdf": "application/pdf",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


class VistaPreviaReporteView(APIView):
    """Genera el reporte y lo devuelve en linea, SIN guardar nada.

    Recorre el mismo camino que el guardado definitivo (`services.generar_documentos`),
    de modo que lo que el usuario ve aqui es exactamente lo que quedaria archivado.
    """

    def post(self, request):
        entrada = GenerarReporteSerializer(
            data=request.data, context={"request": request}
        )
        entrada.is_valid(raise_exception=True)
        datos = entrada.validated_data

        try:
            situaciones = services.resolver_situaciones(
                datos["entidad"], datos["situaciones"]
            )
        except services.SeleccionInvalida as error:
            return Response({"detalle": str(error)}, status=status.HTTP_400_BAD_REQUEST)

        try:
            contenido_docx, contenido_pdf, _ = services.generar_documentos(
                entidad=datos["entidad"],
                situaciones=situaciones,
                fecha_entrega=datos["fecha_entrega"],
                responsable_reporte=datos["responsable_reporte"],
                fecha_corte=datos["fecha_corte"],
            )
        except ErrorConversionPDF as error:
            # 503 y no 500: el documento es correcto, lo que fallo es el conversor.
            return Response(
                {"detalle": str(error)}, status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        formato = datos["formato"]
        contenido = contenido_pdf if formato == "pdf" else contenido_docx
        nombre = services.nombre_archivo(datos["entidad"], datos["fecha_corte"])

        respuesta = HttpResponse(contenido, content_type=TIPOS_MIME[formato])
        respuesta["Content-Disposition"] = f'inline; filename="{nombre}.{formato}"'
        respuesta["Content-Length"] = str(len(contenido))
        return respuesta
