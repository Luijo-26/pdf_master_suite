package com.luisj.pdfmastersuite.ui.screens

import android.net.Uri
import android.widget.Toast
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Image
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import com.luisj.pdfmastersuite.core.models.ImageExportFormat
import com.luisj.pdfmastersuite.core.models.OperationResult
import com.luisj.pdfmastersuite.ui.components.*
import com.luisj.pdfmastersuite.ui.theme.*
import com.luisj.pdfmastersuite.ui.viewmodel.PdfToolViewModel

@Composable
fun PdfToImagesScreen(
    viewModel: PdfToolViewModel,
    onNavigateBack: () -> Unit
) {
    val context = LocalContext.current
    val singleFile by viewModel.singleFile.collectAsState()
    val isLoading by viewModel.isLoading.collectAsState()
    val loadingMsg by viewModel.loadingMessage.collectAsState()
    val result by viewModel.result.collectAsState()

    var selectedFormat by remember { mutableStateOf(ImageExportFormat.PNG) }
    var selectedScale by remember { mutableFloatStateOf(2.0f) }

    val filePicker = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.OpenDocument()
    ) { uri: Uri? ->
        if (uri != null) {
            viewModel.setSingleFile(context, uri)
        }
    }

    val saveFileLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.CreateDocument(
            if (singleFile?.pageCount == 1) selectedFormat.mimeType else "application/zip"
        )
    ) { outputUri: Uri? ->
        if (outputUri != null) {
            context.contentResolver.openOutputStream(outputUri)?.let { stream ->
                viewModel.pdfToImages(context, selectedFormat, selectedScale, stream)
            }
        }
    }

    LaunchedEffect(result) {
        when (val res = result) {
            is OperationResult.Success -> {
                Toast.makeText(context, res.message, Toast.LENGTH_LONG).show()
                viewModel.clearResult()
            }
            is OperationResult.Error -> {
                Toast.makeText(context, res.message, Toast.LENGTH_LONG).show()
                viewModel.clearResult()
            }
            null -> {}
        }
    }

    Scaffold(
        containerColor = BgDark,
        topBar = {
            AppTopBar(
                title = "PDF a Imágenes",
                canNavigateBack = true,
                onNavigateBack = {
                    viewModel.clearState()
                    onNavigateBack()
                }
            )
        }
    ) { paddingValues ->
        Box(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
        ) {
            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(16.dp),
                verticalArrangement = Arrangement.spacedBy(16.dp)
            ) {
                if (singleFile == null) {
                    FilePickerZone(
                        title = "Seleccionar PDF a Convertir",
                        subtitle = "Exporta cada página como imagen JPG o PNG de alta fidelidad",
                        onClick = { filePicker.launch(arrayOf("application/pdf")) }
                    )
                } else {
                    val file = singleFile!!
                    Card(
                        modifier = Modifier
                            .fillMaxWidth()
                            .border(1.dp, BorderDark, RoundedCornerShape(12.dp)),
                        colors = CardDefaults.cardColors(containerColor = SurfaceCard)
                    ) {
                        Column(modifier = Modifier.padding(16.dp)) {
                            Text(
                                text = file.name,
                                style = MaterialTheme.typography.titleMedium,
                                color = TextPrimary
                            )
                            Spacer(modifier = Modifier.height(4.dp))
                            Text(
                                text = "${file.sizeFormatted} • ${file.pageCount ?: "?"} páginas",
                                style = MaterialTheme.typography.bodyMedium,
                                color = TextSecondary
                            )
                            Spacer(modifier = Modifier.height(8.dp))
                            OutlinedButton(onClick = { filePicker.launch(arrayOf("application/pdf")) }) {
                                Text("Cambiar archivo")
                            }
                        }
                    }

                    // Selector de Formato
                    Card(
                        modifier = Modifier
                            .fillMaxWidth()
                            .border(1.dp, BorderDark, RoundedCornerShape(12.dp)),
                        colors = CardDefaults.cardColors(containerColor = SurfaceDark)
                    ) {
                        Column(modifier = Modifier.padding(16.dp)) {
                            Text(
                                text = "Formato de Imagen",
                                style = MaterialTheme.typography.titleSmall,
                                color = TextPrimary
                            )
                            Spacer(modifier = Modifier.height(8.dp))
                            Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                                FilterChip(
                                    selected = selectedFormat == ImageExportFormat.PNG,
                                    onClick = { selectedFormat = ImageExportFormat.PNG },
                                    label = { Text("PNG (Sin pérdida)") }
                                )
                                FilterChip(
                                    selected = selectedFormat == ImageExportFormat.JPEG,
                                    onClick = { selectedFormat = ImageExportFormat.JPEG },
                                    label = { Text("JPG (Comprimido)") }
                                )
                            }
                        }
                    }

                    // Selector de Calidad / Escala
                    Card(
                        modifier = Modifier
                            .fillMaxWidth()
                            .border(1.dp, BorderDark, RoundedCornerShape(12.dp)),
                        colors = CardDefaults.cardColors(containerColor = SurfaceDark)
                    ) {
                        Column(modifier = Modifier.padding(16.dp)) {
                            Text(
                                text = "Resolución de Salida",
                                style = MaterialTheme.typography.titleSmall,
                                color = TextPrimary
                            )
                            Spacer(modifier = Modifier.height(8.dp))
                            Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                                FilterChip(
                                    selected = selectedScale == 1.5f,
                                    onClick = { selectedScale = 1.5f },
                                    label = { Text("Media (110 DPI)") }
                                )
                                FilterChip(
                                    selected = selectedScale == 2.0f,
                                    onClick = { selectedScale = 2.0f },
                                    label = { Text("Alta (150 DPI)") }
                                )
                                FilterChip(
                                    selected = selectedScale == 3.0f,
                                    onClick = { selectedScale = 3.0f },
                                    label = { Text("Ultra (220 DPI)") }
                                )
                            }
                        }
                    }

                    Spacer(modifier = Modifier.weight(1f))

                    val defaultFileName = if (file.pageCount == 1) {
                        "${file.name.removeSuffix(".pdf")}.${selectedFormat.extension}"
                    } else {
                        "${file.name.removeSuffix(".pdf")}_imagenes.zip"
                    }

                    Button(
                        onClick = { saveFileLauncher.launch(defaultFileName) },
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(52.dp),
                        shape = RoundedCornerShape(12.dp),
                        colors = ButtonDefaults.buttonColors(containerColor = AccentGreen)
                    ) {
                        Icon(imageVector = Icons.Default.Image, contentDescription = null)
                        Spacer(modifier = Modifier.width(8.dp))
                        val btnText = if (file.pageCount == 1) {
                            "Exportar Página a ${selectedFormat.extension.uppercase()}"
                        } else {
                            "Exportar ${file.pageCount} Páginas a ZIP"
                        }
                        Text(btnText, style = MaterialTheme.typography.titleMedium)
                    }
                }
            }

            if (isLoading) {
                ProcessingDialog(message = loadingMsg)
            }
        }
    }
}
