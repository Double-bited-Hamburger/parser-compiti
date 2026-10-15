package it.registro.app

import android.Manifest
import android.annotation.SuppressLint
import android.app.Activity
import android.content.ActivityNotFoundException
import android.content.Intent
import android.content.pm.PackageManager
import android.content.res.Configuration
import android.os.Build
import android.os.Bundle
import android.text.TextUtils
import android.webkit.CookieManager
import android.webkit.WebChromeClient
import android.webkit.WebResourceRequest
import android.webkit.WebView
import android.webkit.WebViewClient
import android.widget.FrameLayout
import android.widget.Toast
import androidx.core.content.FileProvider
import androidx.core.view.ViewCompat
import androidx.core.view.WindowCompat
import androidx.core.view.WindowInsetsCompat
import java.io.File
import java.net.HttpURLConnection
import java.net.URL
import kotlin.concurrent.thread

/** L'unica schermata: la pagina dell'app, servita dal server Python interno. */
class MainActivity : Activity() {
    private lateinit var pagina: WebView
    private var porta = 0

    @SuppressLint("SetJavaScriptEnabled")
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        pagina = WebView(this)
        val cornice = FrameLayout(this).apply {
            setBackgroundColor(getColor(R.color.sfondo))
            addView(pagina)
        }
        setContentView(cornice)

        // L'app arriva fino ai bordi dello schermo: si lascia libero lo spazio di barre di sistema e tastiera.
        WindowCompat.setDecorFitsSystemWindows(window, false)
        ViewCompat.setOnApplyWindowInsetsListener(cornice) { vista, margini ->
            val m = margini.getInsets(WindowInsetsCompat.Type.systemBars() or WindowInsetsCompat.Type.displayCutout() or WindowInsetsCompat.Type.ime())
            vista.setPadding(m.left, m.top, m.right, m.bottom)
            WindowInsetsCompat.CONSUMED
        }
        val scuro = resources.configuration.uiMode and Configuration.UI_MODE_NIGHT_MASK == Configuration.UI_MODE_NIGHT_YES
        WindowCompat.getInsetsController(window, cornice).apply {
            isAppearanceLightStatusBars = !scuro
            isAppearanceLightNavigationBars = !scuro
        }

        pagina.setBackgroundColor(getColor(R.color.sfondo))
        pagina.settings.apply {
            javaScriptEnabled = true
            domStorageEnabled = true  // la pagina ricorda lì la scheda aperta
            allowFileAccess = false
            allowContentAccess = false
        }
        pagina.webChromeClient = WebChromeClient()  // senza, le domande di conferma della pagina non comparirebbero
        pagina.webViewClient = object : WebViewClient() {
            override fun shouldOverrideUrlLoading(vista: WebView, richiesta: WebResourceRequest): Boolean {
                val indirizzo = richiesta.url
                if (indirizzo.scheme != "http" || indirizzo.host != "127.0.0.1" || indirizzo.port != porta) {
                    apri(Intent(Intent.ACTION_VIEW, indirizzo))  // i collegamenti esterni vanno al browser
                    return true
                }
                if (indirizzo.path in PDF) {
                    apriPdf(indirizzo.toString())  // la WebView non sa mostrare i PDF: li apre il lettore del telefono
                    return true
                }
                return false
            }
        }

        // Da Android 13 le notifiche vanno chieste: senza, il resto dell'app funziona uguale.
        if (Build.VERSION.SDK_INT >= 33 && checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED) {
            requestPermissions(arrayOf(Manifest.permission.POST_NOTIFICATIONS), 1)
        }

        val app = application as App
        thread {
            try {
                val pronta = app.porta.get()
                runOnUiThread { carica(pronta, app.gettone) }
            } catch (errore: Exception) {
                val dettagli = TextUtils.htmlEncode((errore.cause ?: errore).toString())
                runOnUiThread { pagina.loadData("<h3>L'app non è riuscita ad avviarsi</h3><pre style=\"white-space:pre-wrap\">$dettagli</pre>", "text/html", "utf-8") }
            }
        }
    }

    /** Uscendo dall'app i widget si allineano: un compito spuntato sparisce subito anche da lì. */
    override fun onPause() {
        super.onPause()
        Lavori.aggiornaWidget(this)
    }

    private fun carica(pronta: Int, gettone: String) {
        porta = pronta
        val indirizzo = "http://127.0.0.1:$porta"
        CookieManager.getInstance().apply {
            setAcceptCookie(true)
            setCookie(indirizzo, "gettone=$gettone; Path=/; HttpOnly; SameSite=Strict")
            flush()
        }
        pagina.loadUrl("$indirizzo/")
    }

    private fun apriPdf(indirizzo: String) {
        Toast.makeText(this, R.string.preparo_pdf, Toast.LENGTH_SHORT).show()
        thread {
            try {
                val connessione = (URL(indirizzo).openConnection() as HttpURLConnection).apply {
                    setRequestProperty("Cookie", CookieManager.getInstance().getCookie(indirizzo).orEmpty())
                    connectTimeout = 10_000
                    readTimeout = 60_000
                }
                if (connessione.responseCode != 200) throw IllegalStateException()
                val file = File(File(cacheDir, "pdf").apply { mkdirs() }, "registro.pdf")
                connessione.inputStream.use { origine -> file.outputStream().use { origine.copyTo(it) } }
                val uri = FileProvider.getUriForFile(this, "$packageName.file", file)
                runOnUiThread { apri(Intent(Intent.ACTION_VIEW).setDataAndType(uri, "application/pdf").addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)) }
            } catch (_: Exception) {
                runOnUiThread { Toast.makeText(this, R.string.pdf_non_riuscito, Toast.LENGTH_LONG).show() }
            }
        }
    }

    private fun apri(intento: Intent) {
        try {
            startActivity(intento)
        } catch (_: ActivityNotFoundException) {
            Toast.makeText(this, R.string.nessuna_app, Toast.LENGTH_LONG).show()
        }
    }

    private companion object {
        val PDF = setOf("/api/pdf", "/api/esporta-compiti")
    }
}
