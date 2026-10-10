package com.luisj.pdfmastersuite

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.activity.viewModels
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.ui.Modifier
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import com.luisj.pdfmastersuite.core.PdfEngine
import com.luisj.pdfmastersuite.ui.screens.*
import com.luisj.pdfmastersuite.ui.theme.PDFMasterSuiteTheme
import com.luisj.pdfmastersuite.ui.viewmodel.PdfToolViewModel

class MainActivity : ComponentActivity() {

    private val viewModel: PdfToolViewModel by viewModels()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()

        // Inicializar motor de PDF
        PdfEngine.init(applicationContext)

        setContent {
            PDFMasterSuiteTheme {
                androidx.compose.runtime.LaunchedEffect(Unit) {
                    viewModel.checkForUpdates("2.2.0")
                }

                Surface(
                    modifier = Modifier.fillMaxSize(),
                    color = MaterialTheme.colorScheme.background
                ) {
                    val navController = rememberNavController()

                    NavHost(navController = navController, startDestination = "home") {
                        composable("home") {
                            HomeScreen(
                                viewModel = viewModel,
                                onNavigateToMerge = { navController.navigate("merge") },
                                onNavigateToSplit = { navController.navigate("split") },
                                onNavigateToOrganize = { navController.navigate("organize") },
                                onNavigateToImagesToPdf = { navController.navigate("images_to_pdf") },
                                onNavigateToCompress = { navController.navigate("compress") },
                                onNavigateToSecurity = { navController.navigate("security") },
                                onNavigateToPdfToImages = { navController.navigate("pdf_to_images") },
                                onNavigateToWatermark = { navController.navigate("watermark") },
                                onNavigateToPageNumbers = { navController.navigate("page_numbers") },
                                onNavigateToRotateBulk = { navController.navigate("rotate_bulk") },
                                onNavigateToPdfToText = { navController.navigate("pdf_to_text") },
                                onNavigateToCrop = { navController.navigate("crop") },
                                onNavigateToSign = { navController.navigate("sign") }
                            )
                        }

                        composable("merge") {
                            MergeScreen(
                                viewModel = viewModel,
                                onNavigateBack = { navController.popBackStack() }
                            )
                        }

                        composable("split") {
                            SplitScreen(
                                viewModel = viewModel,
                                onNavigateBack = { navController.popBackStack() }
                            )
                        }

                        composable("organize") {
                            PageGridScreen(
                                viewModel = viewModel,
                                onNavigateBack = { navController.popBackStack() }
                            )
                        }

                        composable("images_to_pdf") {
                            ImagesToPdfScreen(
                                viewModel = viewModel,
                                onNavigateBack = { navController.popBackStack() }
                            )
                        }

                        composable("compress") {
                            CompressScreen(
                                viewModel = viewModel,
                                onNavigateBack = { navController.popBackStack() }
                            )
                        }

                        composable("security") {
                            SecurityScreen(
                                viewModel = viewModel,
                                onNavigateBack = { navController.popBackStack() }
                            )
                        }

                        // NUEVAS PANTALLAS V2.2
                        composable("pdf_to_images") {
                            PdfToImagesScreen(
                                viewModel = viewModel,
                                onNavigateBack = { navController.popBackStack() }
                            )
                        }

                        composable("watermark") {
                            WatermarkScreen(
                                viewModel = viewModel,
                                onNavigateBack = { navController.popBackStack() }
                            )
                        }

                        composable("page_numbers") {
                            PageNumbersScreen(
                                viewModel = viewModel,
                                onNavigateBack = { navController.popBackStack() }
                            )
                        }

                        composable("rotate_bulk") {
                            RotateBulkScreen(
                                viewModel = viewModel,
                                onNavigateBack = { navController.popBackStack() }
                            )
                        }

                        composable("pdf_to_text") {
                            PdfToTextScreen(
                                viewModel = viewModel,
                                onNavigateBack = { navController.popBackStack() }
                            )
                        }

                        composable("crop") {
                            CropScreen(
                                viewModel = viewModel,
                                onNavigateBack = { navController.popBackStack() }
                            )
                        }

                        composable("sign") {
                            SignScreen(
                                viewModel = viewModel,
                                onNavigateBack = { navController.popBackStack() }
                            )
                        }
                    }
                }
            }
        }
    }
}
