package it.registro.app

import android.app.AlarmManager
import android.app.PendingIntent
import android.appwidget.AppWidgetManager
import android.appwidget.AppWidgetProvider
import android.content.ComponentName
import android.content.Context
import android.content.Intent
import android.graphics.Bitmap
import android.os.SystemClock
import android.view.View
import android.widget.RemoteViews
import com.chaquo.python.Python
import org.json.JSONObject

/** Widget 4×2: compiti per il prossimo giorno di scuola. Il disegno vero lo fa [Widget.aggiorna], in sottofondo. */
class WidgetCompiti : AppWidgetProvider() {
    override fun onUpdate(contesto: Context, gestore: AppWidgetManager, id: IntArray) = Lavori.aggiornaWidget(contesto)
}

/** Widget 2×2: giorni alla prossima verifica. */
class WidgetVerifica : AppWidgetProvider() {
    override fun onUpdate(contesto: Context, gestore: AppWidgetManager, id: IntArray) = Lavori.aggiornaWidget(contesto)
}

/** Widget 4×1: la lezione in corso (o la prossima). Si ridisegna anche da sé quando l'ora cambia. */
class WidgetAdesso : AppWidgetProvider() {
    override fun onUpdate(contesto: Context, gestore: AppWidgetManager, id: IntArray) = Lavori.aggiornaWidget(contesto)

    override fun onReceive(contesto: Context, intento: Intent) {
        if (intento.action == Widget.CAMBIO_ORA) Lavori.aggiornaWidget(contesto) else super.onReceive(contesto, intento)
    }
}

object Widget {
    const val CAMBIO_ORA = "it.registro.app.CAMBIO_ORA"

    /** Chiede il riassunto a Python (notifiche.widget) e ridisegna tutti i widget. Fuori dal thread principale, a server avviato. */
    fun aggiorna(contesto: Context) {
        val gestore = AppWidgetManager.getInstance(contesto)
        val compiti = gestore.getAppWidgetIds(ComponentName(contesto, WidgetCompiti::class.java))
        val verifica = gestore.getAppWidgetIds(ComponentName(contesto, WidgetVerifica::class.java))
        val adesso = gestore.getAppWidgetIds(ComponentName(contesto, WidgetAdesso::class.java))
        if (compiti.isEmpty() && verifica.isEmpty() && adesso.isEmpty()) return
        val dati = JSONObject(Python.getInstance().getModule("notifiche").callAttr("widget").toString())
        val apri = Notifiche.apriApp(contesto)
        val veste = Veste(contesto, dati.optString("tema") == "ultra")
        if (compiti.isNotEmpty()) gestore.updateAppWidget(compiti, compiti(contesto, dati, apri, veste))
        if (verifica.isNotEmpty()) gestore.updateAppWidget(verifica, verifica(contesto, dati, apri, veste))
        if (adesso.isNotEmpty()) gestore.updateAppWidget(adesso, adesso(contesto, dati, apri, veste))
    }

    /**
     * L'aspetto dei widget segue il tema dell'app: col tema «Ultra» sono la lattina bianca (sfondo con rose e alloro,
     * graffi argentati, numeri neri «strappati», lineetta azzurra); con tutti gli altri, lo stile Nothing a puntini.
     */
    private class Veste(val c: Context, val ultra: Boolean) {
        fun numero(testo: String, altezzaDp: Float): Bitmap = if (ultra) Lattina.numero(testo, c, altezzaDp) else PuntiMatrice.disegna(testo, c)

        /** Da chiamare per ultima: i colori qui sostituiscono quelli del layout (che in tema scuro sarebbero chiari). */
        fun vesti(v: RemoteViews, sfondo: Int, numeri: List<Int>, principali: List<Int>, secondari: List<Int>, conLinea: Boolean): RemoteViews {
            if (!ultra) return v
            v.setInt(R.id.radice, "setBackgroundResource", sfondo)
            v.setViewVisibility(R.id.punto, View.GONE)
            if (conLinea) v.setViewVisibility(R.id.linea, View.VISIBLE)
            numeri.forEach { v.setInt(it, "setColorFilter", c.getColor(R.color.ultra_testo)) }
            principali.forEach { v.setTextColor(it, c.getColor(R.color.ultra_testo)) }
            secondari.forEach { v.setTextColor(it, c.getColor(R.color.ultra_tenue)) }
            return v
        }
    }

    private fun adesso(c: Context, dati: JSONObject, apri: PendingIntent, veste: Veste): RemoteViews {
        val v = RemoteViews(c.packageName, R.layout.widget_adesso)
        v.setOnClickPendingIntent(R.id.radice, apri)
        val fine = {
            veste.vesti(v, R.drawable.widget_sfondo_ultra_adesso, listOf(R.id.orario), listOf(R.id.materia),
                listOf(R.id.etichetta, R.id.conto, R.id.dopo), conLinea = false)
        }
        val lezione = dati.optJSONObject("adesso")
        if (lezione == null) {
            v.setImageViewBitmap(R.id.orario, veste.numero("--:--", 30f))
            v.setTextViewText(R.id.materia, c.getString(if (dati.optBoolean("vuoto")) R.string.widget_apri_app else R.string.widget_adesso_nessuna))
            v.setViewVisibility(R.id.conto, View.GONE)
            return fine()
        }
        val inCorso = lezione.getString("stato") == "ora"
        v.setImageViewBitmap(R.id.orario, veste.numero(lezione.getString("orario"), 30f))
        v.setContentDescription(R.id.orario, lezione.getString("orario"))
        v.setTextViewText(R.id.etichetta, if (inCorso) c.getString(R.string.widget_adesso_titolo) else c.getString(R.string.widget_adesso_prossima, lezione.getString("quando")))
        v.setTextViewText(R.id.materia, lezione.getString("materia"))
        v.setTextViewText(R.id.dopo, lezione.optString("dopo").takeIf { it.isNotEmpty() }?.let { c.getString(R.string.widget_poi, it) } ?: "")
        // Il conto alla rovescia lo tiene il launcher (Chronometer): avanza da solo, senza ridisegnare il widget ogni minuto.
        val mancano = (lezione.getDouble("istante") * 1000).toLong() - System.currentTimeMillis()
        if (mancano in 1 until 12 * 3600_000L) {
            v.setViewVisibility(R.id.conto, View.VISIBLE)
            v.setChronometer(R.id.conto, SystemClock.elapsedRealtime() + mancano, c.getString(R.string.widget_mancano), true)
            v.setChronometerCountDown(R.id.conto, true)
        } else {
            v.setViewVisibility(R.id.conto, View.GONE)
        }
        sveglia(c, (lezione.getDouble("cambio") * 1000).toLong())
        return fine()
    }

    /** Ridisegna il widget «Adesso» poco dopo il prossimo cambio d'ora (sveglia non esatta: niente permessi speciali). */
    private fun sveglia(c: Context, quando: Long) {
        val intento = PendingIntent.getBroadcast(
            c, 7, Intent(c, WidgetAdesso::class.java).setAction(CAMBIO_ORA),
            PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT,
        )
        c.getSystemService(AlarmManager::class.java).set(AlarmManager.RTC, quando + 30_000, intento)
    }

    private fun compiti(c: Context, dati: JSONObject, apri: PendingIntent, veste: Veste): RemoteViews {
        val v = RemoteViews(c.packageName, R.layout.widget_compiti)
        v.setOnClickPendingIntent(R.id.radice, apri)
        val fine = {
            veste.vesti(v, R.drawable.widget_sfondo_ultra_compiti, listOf(R.id.numero), listOf(R.id.elenco),
                listOf(R.id.intestazione), conLinea = true)
        }
        val compiti = dati.optJSONObject("compiti")
        if (dati.optBoolean("vuoto") || compiti == null) {
            v.setImageViewBitmap(R.id.numero, veste.numero("--", 48f))
            v.setTextViewText(R.id.elenco, c.getString(R.string.widget_apri_app))
            return fine()
        }
        val daFare = compiti.getJSONArray("da_fare")
        val materie = (0 until daFare.length()).map { daFare.getJSONObject(it).getString("materia") }
        v.setTextViewText(R.id.intestazione, c.getString(R.string.widget_compiti_titolo, compiti.getString("quando")))
        v.setImageViewBitmap(R.id.numero, veste.numero(materie.size.toString().padStart(2, '0'), 48f))
        v.setContentDescription(R.id.numero, materie.size.toString())
        v.setTextViewText(R.id.elenco, when {
            materie.isNotEmpty() -> materie.joinToString("\n")
            compiti.getInt("totale") > 0 -> c.getString(R.string.widget_tutto_fatto)
            else -> c.getString(R.string.widget_niente)
        })
        return fine()
    }

    private fun verifica(c: Context, dati: JSONObject, apri: PendingIntent, veste: Veste): RemoteViews {
        val v = RemoteViews(c.packageName, R.layout.widget_verifica)
        v.setOnClickPendingIntent(R.id.radice, apri)
        val fine = {
            veste.vesti(v, R.drawable.widget_sfondo_ultra_verifica, listOf(R.id.giorni), listOf(R.id.materia),
                listOf(R.id.titolo, R.id.giorni_etichetta, R.id.quando), conLinea = true)
        }
        if (dati.optBoolean("vuoto")) {
            v.setImageViewBitmap(R.id.giorni, veste.numero("--", 40f))
            return fine()
        }
        val prossima = dati.optJSONObject("verifica")
        if (prossima == null) {
            v.setImageViewBitmap(R.id.giorni, veste.numero("--", 40f))
            v.setTextViewText(R.id.giorni_etichetta, "")
            v.setTextViewText(R.id.materia, c.getString(R.string.widget_nessuna))
            v.setTextViewText(R.id.quando, c.getString(R.string.widget_in_vista))
            return fine()
        }
        val giorni = prossima.getInt("giorni")
        v.setImageViewBitmap(R.id.giorni, veste.numero(if (giorni == 0) "OGGI" else giorni.toString().padStart(2, '0'), 40f))
        v.setContentDescription(R.id.giorni, giorni.toString())
        // Stile Nothing: rosso all'ultimo giorno (vale in tema chiaro e scuro). Col tema Ultra resta nero: lì l'unico colore è l'azzurro.
        if (giorni <= 1 && !veste.ultra) v.setInt(R.id.giorni, "setColorFilter", c.getColor(R.color.widget_rosso))
        v.setTextViewText(R.id.giorni_etichetta, when (giorni) { 0 -> ""; 1 -> c.getString(R.string.widget_giorno); else -> c.getString(R.string.widget_giorni) })
        v.setTextViewText(R.id.materia, prossima.getString("materia"))
        val altre = prossima.optInt("altre")
        v.setTextViewText(R.id.quando, prossima.getString("quando") + if (altre > 0) "  " + c.getString(R.string.widget_altre, altre) else "")
        return fine()
    }
}
