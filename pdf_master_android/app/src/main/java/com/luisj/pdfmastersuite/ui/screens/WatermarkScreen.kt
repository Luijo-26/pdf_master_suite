package com.luisj.pdfmastersuite.ui.screens

import android.net.Uri
import android.widget.Toast
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.BrandingWatermark
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import com.luisj.pdfmastersuite.core.models.OperationResult
import com.luisj.pdfmastersuite.core.models.WatermarkPosition
import com.luisj.pdfmastersuite.ui.components.*
import com.luisj.pdfmastersuite.ui.theme.*
import com.luisj.pdfmastersuite.ui.viewmodel.PdfToolViewModel

@Composable
fun WatermarkScreen(
    viewModel: PdfToolViewModel,
    onNavigateBack: () -> Unit
) {
    val context = LocalContext.current
    val singleFile by viewModel.singleFile.collectAsState()
    val isLoading by viewModel.isLoading.collectAsState()
    val loadingMsg by viewModel.loadingMessage.collectAsState()
    val result by viewModel.result.collectAsState()

    var watermarkText by remember { mutableStateOf("CONFIDENCIAL") }
    var opacity by remember { mutableFloatStateOf(0.35f) }
    var selectedPosition by remember { mutableStateOf(WatermarkPosition.DIAGONAL) }
    var fontSize by remember { mutableFloatStateOf(48f) }
    var selectedImageUri by remember { mutableStateOf<Uri?>(null) }

    val filePicker = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.OpenDocument()
    ) { uri: Uri? ->
        if (uri != null) {
            viewModel.setSingleFile(context, uri)
        }
    }

    val imagePicker = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.GetContent()
    ) { uri: Uri? ->
        selectedImageUri = uri
    }

    val saveFileLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.CreateDocument("application/pdf")
    ) { outputUri: Uri? ->
        if (outputUri != null) {
            context.contentResolver.openOutputStream(outputUri)?.let { stream ->
                val angle = if (selectedPosition == WatermarkPosition.DIAGONAL) 45f else 0f
                viewModel.addWatermark(
                    context = context,
                    text = watermarkText,
                    imageUri = selectedImageUri,
                    opacity = opacity,
                    angleDegrees = angle,
                    fontSize = fontSize,
                    position = selectedPosition,
                    outputStream = stream
                )
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
                title = "Marca de Agua",
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
                    .padding(16.dp)
                    .verticalScroll(rememberScrollState()),
                verticalArrangement = Arrangement.spacedBy(16.dp)
            ) {
                if (singleFile == null) {
                    FilePickerZone(
                        title = "Seleccionar PDF para Marca de Agua",
                        subtitle = "Inserta sellos de texto o imágenes corporativas en todas las páginas",
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

                    // Configuración de Texto / Imagen
                    Card(
                        modifier = Modifier
                            .fillMaxWidth()
                            .border(1.dp, BorderDark, RoundedCornerShape(12.dp)),
                        colors = CardDefaults.cardColors(containerColor = SurfaceDark)
                    ) {
                        Column(modifier = Modifier.padding(16.dp)) {
                            Text(
                                text = "Contenido de la Marca de Agua",
                                style = MaterialTheme.typography.titleSmall,
                                color = TextPrimary
                            )
                            Spacer(modifier = Modifier.height(10.dp))

                            OutlinedTextField(
                                value = watermarkText,
                                onValueChange = { watermarkText = it },
                                label = { Text("Texto de la marca") },
                                singleLine = true,
                                modifier = Modifier.fillMaxWidth(),
                                enabled = selectedImageUri == null
                            )

                            Spacer(modifier = Modifier.height(10.dp))

                            Row(
                                modifier = Modifier.fillMaxWidth(),
                                horizontalArrangement = Arrangement.SpaceBetween
                            ) {
                                OutlinedButton(onClick = { imagePicker.launch("image/*") }) {
                                    Text(if (selectedImageUri != null) "Imagen seleccionada" else "Usar logo de imagen")
                                }
                                if (selectedImageUri != null) {
                                    TextButton(onClick = { selectedImageUri = null }) {
                                        Text("Quitar imagen", color = AccentRed)
                                    }
                                }
                            }
                        }
                    }

                    // Posición y Opacidad
                    Card(
                        modifier = Modifier
                            .fillMaxWidth()
                            .border(1.dp, BorderDark, RoundedCornerShape(12.dp)),
                        colors = CardDefaults.cardColors(containerColor = SurfaceDark)
                    ) {
                        Column(modifier = Modifier.padding(16.dp)) {
                            Text(
                                text = "Disposición y Transparencia",
                                style = MaterialTheme.typography.titleSmall,
                                color = TextPrimary
                            )
                            Spacer(modifier = Modifier.height(10.dp))

                            Text(
                                text = "Opacidad: ${(opacity * 100).toInt()}%",
                                style = MaterialTheme.typography.bodyMedium,
                                color = TextSecondary
                            )
                            Slider(
                                value = opacity,
                                onValueChange = { opacity = it },
                                valueRange = 0.10f..0.90f,
                                steps = 7
                            )

                            Spacer(modifier = Modifier.height(10.dp))
                            Text(
                                text = "Posición en página",
                                style = MaterialTheme.typography.bodyMedium,
                                color = TextSecondary
                            )
                            Spacer(modifier = Modifier.height(6.dp))
                            Row(
                                modifier = Modifier.fillMaxWidth(),
                                horizontalArrangement = Arrangement.spacedBy(8.dp)
                            ) {
                                FilterChip(
                                    selected = selectedPosition == WatermarkPosition.DIAGONAL,
                                    onClick = { selectedPosition = WatermarkPosition.DIAGONAL },
                                    label = { Text("Diagonal") }
                                )
                                FilterChip(
                                    selected = selectedPosition == WatermarkPosition.CENTER,
                                    onClick = { selectedPosition = WatermarkPosition.CENTER },
                                    label = { Text("Centro") }
                                )
                                FilterChip(
                                    selected = selectedPosition == WatermarkPosition.TOP_CENTER,
                                    onClick = { selectedPosition = WatermarkPosition.TOP_CENTER },
                                    label = { Text("Arriba") }
                                )
                            }
                        }
                    }

                    Spacer(modifier = Modifier.height(8.dp))

                    Button(
                        onClick = { saveFileLauncher.launch("PDF_Con_MarcaAgua.pdf") },
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(52.dp),
                        shape = RoundedCornerShape(12.dp),
                        colors = ButtonDefaults.buttonColors(containerColor = AccentPurple)
                    ) {
                        Icon(imageVector = Icons.Default.BrandingWatermark, contentDescription = null)
                        Spacer(modifier = Modifier.width(8.dp))
                        Text("Aplicar y Guardar PDF", style = MaterialTheme.typography.titleMedium)
                    }

                    Spacer(modifier = Modifier.height(16.dp))
                }
            }

            if (isLoading) {
                ProcessingDialog(message = loadingMsg)
            }
        }
    }
}
