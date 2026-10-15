package it.registro.app

import android.app.Application
import android.security.keystore.KeyGenParameterSpec
import android.security.keystore.KeyProperties
import android.util.Base64
import com.chaquo.python.Python
import com.chaquo.python.android.AndroidPlatform
import java.io.File
import java.security.KeyStore
import java.security.SecureRandom
import java.util.concurrent.Executors
import java.util.concurrent.Future
import javax.crypto.Cipher
import javax.crypto.KeyGenerator
import javax.crypto.SecretKey
import javax.crypto.spec.GCMParameterSpec

/** Avvia una sola volta per processo il server Python dell'app (lo stesso del PC) e ne ricorda porta e gettone. */
class App : Application() {
    /** Segreto di questo avvio: la pagina lo presenta come cookie, le altre app del telefono non lo conoscono. */
    val gettone: String = casuale(24)

    /** La porta su cui risponde il server; l'avvio avviene in sottofondo per non bloccare l'apertura dell'app. */
    lateinit var porta: Future<Int>
        private set

    override fun onCreate() {
        super.onCreate()
        porta = Executors.newSingleThreadExecutor().submit<Int> { avviaServer() }
        Notifiche.creaCanali(this)
        Lavori.pianifica(this) // una volta pianificato resta (KEEP): rifarlo a ogni avvio non cambia nulla
    }

    private fun avviaServer(): Int {
        val web = copiaPagina()
        if (!Python.isStarted()) Python.start(AndroidPlatform(this))
        val python = Python.getInstance()
        // Vanno impostate prima che il codice dell'app venga importato: config.py le legge una volta sola.
        val ambiente = python.getModule("os")["environ"]!!
        mapOf(
            "ANDROID_APP" to "1",
            "DATI_DIR" to filesDir.absolutePath,
            "WEB_DIR" to web.absolutePath,
            "GETTONE_LOCALE" to gettone,
            "CHIAVE_CREDENZIALI" to chiaveCredenziali(),
        ).forEach { (nome, valore) -> ambiente.callAttr("__setitem__", nome, valore) }
        return python.getModule("avvio_android").callAttr("avvia").toInt()
    }

    /** La pagina (HTML, CSS, JS) sta negli assets: il server la legge da una cartella vera, quindi la si copia lì. */
    private fun copiaPagina(): File {
        val cartella = File(codeCacheDir, "web").apply { deleteRecursively(); mkdirs() }
        assets.list("web").orEmpty().forEach { nome ->
            assets.open("web/$nome").use { origine -> File(cartella, nome).outputStream().use { origine.copyTo(it) } }
        }
        return cartella
    }

    /**
     * Il segreto con cui Python cifra su disco le password dei registri. Sta nelle preferenze dell'app, a sua volta
     * cifrato con una chiave dell'Android Keystore, che non esce mai dal telefono.
     */
    private fun chiaveCredenziali(): String {
        val preferenze = getSharedPreferences("segreti", MODE_PRIVATE)
        val portachiavi = KeyStore.getInstance("AndroidKeyStore").apply { load(null) }
        if (!portachiavi.containsAlias(ALIAS)) {
            KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES, "AndroidKeyStore").apply {
                init(
                    KeyGenParameterSpec.Builder(ALIAS, KeyProperties.PURPOSE_ENCRYPT or KeyProperties.PURPOSE_DECRYPT)
                        .setBlockModes(KeyProperties.BLOCK_MODE_GCM)
                        .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
                        .build()
                )
                generateKey()
            }
        }
        val chiave = portachiavi.getKey(ALIAS, null) as SecretKey
        preferenze.getString("credenziali", null)?.let { salvato ->
            try {
                val (iv, cifrato) = salvato.split(":").map { Base64.decode(it, Base64.NO_WRAP) }
                val cifrario = Cipher.getInstance(AES_GCM).apply { init(Cipher.DECRYPT_MODE, chiave, GCMParameterSpec(128, iv)) }
                return String(cifrario.doFinal(cifrato))
            } catch (_: Exception) {
                // Chiave del telefono cambiata (per esempio dopo un ripristino): le password andranno reinserite o risincronizzate.
            }
        }
        val segreto = casuale(32)
        val cifrario = Cipher.getInstance(AES_GCM).apply { init(Cipher.ENCRYPT_MODE, chiave) }
        val cifrato = cifrario.doFinal(segreto.toByteArray())
        val testo = listOf(cifrario.iv, cifrato).joinToString(":") { Base64.encodeToString(it, Base64.NO_WRAP) }
        preferenze.edit().putString("credenziali", testo).apply()
        return segreto
    }

    private companion object {
        const val ALIAS = "credenziali-registro"
        const val AES_GCM = "AES/GCM/NoPadding"

        fun casuale(byte: Int): String =
            Base64.encodeToString(ByteArray(byte).also { SecureRandom().nextBytes(it) }, Base64.URL_SAFE or Base64.NO_WRAP or Base64.NO_PADDING)
    }
}
