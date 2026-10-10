package com.luisj.pdfmastersuite.core

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL

data class AppUpdateInfo(
    val latestVersion: String,
    val releaseTitle: String,
    val changelog: String,
    val downloadUrl: String,
    val htmlUrl: String
)

object UpdateChecker {
    private const val GITHUB_REPO = "Luijo-26/pdf_master_suite"
    private const val GITHUB_API_URL = "https://api.github.com/repos/$GITHUB_REPO/releases/latest"
    const val GITHUB_RELEASES_URL = "https://github.com/$GITHUB_REPO/releases"

    fun isNewerVersion(current: String, candidate: String): Boolean {
        val cleanCurrent = current.trim().removePrefix("v").removePrefix("V")
        val cleanCandidate = candidate.trim().removePrefix("v").removePrefix("V")

        fun parseParts(v: String): List<Int> {
            val base = v.split("-")[0]
            return base.split(".").mapNotNull { it.toIntOrNull() }
        }

        val currParts = parseParts(cleanCurrent)
        val candParts = parseParts(cleanCandidate)
        val maxLen = maxOf(currParts.size, candParts.size)

        for (i in 0 until maxLen) {
            val c = currParts.getOrElse(i) { 0 }
            val n = candParts.getOrElse(i) { 0 }
            if (n > c) return true
            if (n < c) return false
        }
        return false
    }

    suspend fun checkForUpdates(currentVersion: String = "2.2.0"): AppUpdateInfo? = withContext(Dispatchers.IO) {
        try {
            val url = URL(GITHUB_API_URL)
            val connection = (url.openConnection() as HttpURLConnection).apply {
                connectTimeout = 6000
                readTimeout = 6000
                setRequestProperty("User-Agent", "PDFMasterSuite-Android/$currentVersion")
                setRequestProperty("Accept", "application/vnd.github.v3+json")
            }

            if (connection.responseCode != 200) {
                return@withContext null
            }

            val responseBody = connection.inputStream.bufferedReader().use { it.readText() }
            val json = JSONObject(responseBody)

            val tagName = json.optString("tag_name", "")
            val cleanVersion = tagName.removePrefix("v").removePrefix("V")
            val name = json.optString("name", "Versión $tagName")
            val body = json.optString("body", "").trim()
            val htmlUrl = json.optString("html_url", GITHUB_RELEASES_URL)

            var downloadUrl = htmlUrl
            val assets = json.optJSONArray("assets")
            if (assets != null) {
                for (i in 0 until assets.length()) {
                    val asset = assets.getJSONObject(i)
                    val assetName = asset.optString("name", "")
                    if (assetName.endsWith(".apk", ignoreCase = true)) {
                        downloadUrl = asset.optString("browser_download_url", downloadUrl)
                        break
                    }
                }
            }

            if (isNewerVersion(currentVersion, cleanVersion)) {
                return@withContext AppUpdateInfo(
                    latestVersion = cleanVersion,
                    releaseTitle = name,
                    changelog = body,
                    downloadUrl = downloadUrl,
                    htmlUrl = htmlUrl
                )
            }
            null
        } catch (_: Exception) {
            null
        }
    }
}
