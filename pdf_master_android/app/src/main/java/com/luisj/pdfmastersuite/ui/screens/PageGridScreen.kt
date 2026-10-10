package com.luisj.pdfmastersuite.ui.screens

import android.graphics.Bitmap
import android.net.Uri
import android.widget.Toast
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.grid.GridCells
import androidx.compose.foundation.lazy.grid.LazyVerticalGrid
import androidx.compose.foundation.lazy.grid.itemsIndexed
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.rotate
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.luisj.pdfmastersuite.core.models.OperationResult
import com.luisj.pdfmastersuite.core.models.PdfPageItem
import com.luisj.pdfmastersuite.ui.components.*
import com.luisj.pdfmastersuite.ui.theme.*
import com.luisj.pdfmastersuite.ui.viewmodel.PdfToolViewModel

@Composable
fun PageGridScreen(
    viewModel: PdfToolViewModel,
    onNavigateBack: () -> Unit
) {
    val context = LocalContext.current
    val singleFile by viewModel.singleFile.collectAsState()
    val pages by viewModel.pdfPages.collectAsState()
    val isLoading by viewModel.isLoading.collectAsState()
    val loadingMsg by viewModel.loadingMessage.collectAsState()
    val result by viewModel.result.collectAsState()

    val filePicker = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.OpenDocument()
    ) { uri: Uri? ->
        if (uri != null) {
            viewModel.setSingleFile(context, uri, loadThumbnails = true)
        }
    }

    val saveFileLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.CreateDocument("application/pdf")
    ) { outputUri: Uri? ->
        if (outputUri != null) {
            context.contentResolver.openOutputStream(outputUri)?.let { stream ->
                viewModel.exportRearranged(context, stream)
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
                title = "Organizar y Rotar",
                canNavigateBack = true,
                onNavigateBack = {
                    viewModel.clearState()
                    onNavigateBack()
                }
            )
        },
        bottomBar = {
            if (pages.isNotEmpty()) {
                val activePagesCount = pages.count { !it.isMarkedForDeletion }
                Surface(
                    color = SurfaceDark,
                    border = androidx.compose.foundation.BorderStroke(1.dp, BorderDark)
                ) {
                    Button(
                        onClick = { saveFileLauncher.launch("PDF_Organizado.pdf") },
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(16.dp)
                            .height(52.dp),
                        shape = RoundedCornerShape(12.dp),
                        colors = ButtonDefaults.buttonColors(containerColor = PrimaryIndigo),
                        enabled = activePagesCount > 0
                    ) {
                        Icon(imageVector = Icons.Default.Save, contentDescription = null)
                        Spacer(modifier = Modifier.width(8.dp))
                        Text("Exportar PDF ($activePagesCount páginas)", style = MaterialTheme.typography.titleMedium)
                    }
                }
            }
        }
    ) { paddingValues ->
        Box(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
        ) {
            if (singleFile == null) {
                Column(
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(16.dp)
                ) {
                    FilePickerZone(
                        title = "Seleccionar PDF para Organizar",
                        subtitle = "Cargará las páginas como miniaturas interactivas",
                        onClick = { filePicker.launch(arrayOf("application/pdf")) }
                    )
                }
            } else {
                Column(modifier = Modifier.fillMaxSize()) {
                    // Encabezado con información del archivo
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(horizontal = 16.dp, vertical = 8.dp),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Text(
                            text = singleFile!!.name,
                            style = MaterialTheme.typography.bodyMedium,
                            color = TextSecondary,
                            modifier = Modifier.weight(1f),
                            maxLines = 1
                        )
                        TextButton(onClick = { filePicker.launch(arrayOf("application/pdf")) }) {
                            Text("Cambiar", color = PrimaryIndigo)
                        }
                    }

                    // Cuadrícula de páginas
                    LazyVerticalGrid(
                        columns = GridCells.Adaptive(minSize = 150.dp),
                        modifier = Modifier
                            .fillMaxSize()
                            .padding(horizontal = 16.dp),
                        verticalArrangement = Arrangement.spacedBy(16.dp),
                        horizontalArrangement = Arrangement.spacedBy(16.dp),
                        contentPadding = PaddingValues(bottom = 90.dp)
                    ) {
                        itemsIndexed(pages) { index, pageItem ->
                            PageCard(
                                item = pageItem,
                                onRotate = { viewModel.rotatePageClockwise(index) },
                                onToggleDelete = { viewModel.toggleDeletePage(index) }
                            )
                        }
                    }
                }
            }

            if (isLoading) {
                ProcessingDialog(message = loadingMsg)
            }
        }
    }
}

@Composable
fun PageCard(
    item: PdfPageItem,
    onRotate: () -> Unit,
    onToggleDelete: () -> Unit
) {
    val isDeleted = item.isMarkedForDeletion
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(12.dp))
            .border(
                width = 1.dp,
                color = if (isDeleted) AccentRed.copy(alpha = 0.5f) else BorderDark,
                shape = RoundedCornerShape(12.dp)
            )
            .alpha(if (isDeleted) 0.4f else 1f),
        colors = CardDefaults.cardColors(containerColor = SurfaceDark)
    ) {
        Column(
            modifier = Modifier.padding(8.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            // Cabecera de la miniatura
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Surface(
                    shape = RoundedCornerShape(4.dp),
                    color = PrimaryIndigo.copy(alpha = 0.2f)
                ) {
                    Text(
                        text = "Pág. ${item.displayPageNumber}",
                        style = MaterialTheme.typography.labelSmall,
                        color = PrimaryIndigo,
                        modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp)
                    )
                }

                if (item.rotationDegrees > 0) {
                    Text(
                        text = "${item.rotationDegrees}°",
                        style = MaterialTheme.typography.labelSmall,
                        color = AccentAmber
                    )
                }
            }

            Spacer(modifier = Modifier.height(8.dp))

            // Imagen de la miniatura rotada
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .height(180.dp)
                    .clip(RoundedCornerShape(8.dp))
                    .background(SurfaceCard),
                contentAlignment = Alignment.Center
            ) {
                if (item.thumbnail != null) {
                    Image(
                        bitmap = item.thumbnail!!.asImageBitmap(),
                        contentDescription = "Página ${item.displayPageNumber}",
                        modifier = Modifier
                            .fillMaxSize()
                            .rotate(item.rotationDegrees.toFloat()),
                        contentScale = ContentScale.Fit
                    )
                } else {
                    CircularProgressIndicator(modifier = Modifier.size(24.dp))
                }
            }

            Spacer(modifier = Modifier.height(8.dp))

            // Botones de acción (Rotar + Eliminar)
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceEvenly
            ) {
                IconButton(onClick = onRotate, enabled = !isDeleted) {
                    Icon(
                        imageVector = Icons.Default.RotateRight,
                        contentDescription = "Rotar 90 grados",
                        tint = if (!isDeleted) TextPrimary else TextMuted
                    )
                }

                IconButton(onClick = onToggleDelete) {
                    Icon(
                        imageVector = if (isDeleted) Icons.Default.Restore else Icons.Default.DeleteOutline,
                        contentDescription = if (isDeleted) "Restaurar" else "Eliminar",
                        tint = if (isDeleted) AccentGreen else AccentRed
                    )
                }
            }
        }
    }
}
