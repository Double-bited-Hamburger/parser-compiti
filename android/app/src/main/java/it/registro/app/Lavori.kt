package it.registro.app

import android.Manifest
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Build
import androidx.core.app.NotificationChannelCompat
import androidx.core.app.NotificationCompat
import androidx.core.app.NotificationManagerCompat
import androidx.work.Constraints
import androidx.work.ExistingPeriodicWorkPolicy
import androidx.work.ExistingWorkPolicy
import androidx.work.NetworkType
import androidx.work.OneTimeWorkRequestBuilder
import androidx.work.PeriodicWorkRequestBuilder
import androidx.work.WorkManager
import androidx.work.Worker
import androidx.work.WorkerParameters
import com.chaquo.python.Python
import org.json.JSONArray
import org.json.JSONObject
import java.util.concurrent.TimeUnit

/** Ogni due ore: riscarica i registri, avvisa delle novità (notifiche.controlla) e ridisegna i widget. */
class ControlloWorker(contesto: Context, parametri: WorkerParameters) : Worker(contesto, parametri) {
    override fun doWork(): Result {
        val app = applicationContext as App
        try {
            app.porta.get() // il server Python è avviato: si può usare lo stesso codice (e lo stesso BLOCCO)
            val avvisi = JSONArray(Python.getInstance().getModule("notifiche").callAttr("controlla").toString())
            for (i in 0 until avvisi.length()) Notifiche.mostra(app, avvisi.getJSONObject(i))
            Widget.aggiorna(app)
        } catch (_: Exception) {
            // Registro irraggiungibile o errore imprevisto (Python lo annota in cache/errori.log): si riprova al prossimo giro.
        }
        return Result.success()
    }
}

/** Solo i widget, dai dati già scaricati: quando se ne aggiunge uno o si chiude l'app. */
class WidgetWorker(contesto: Context, parametri: WorkerParameters) : Worker(contesto, parametri) {
    override fun doWork(): Result {
        try {
            (applicationContext as App).porta.get()
            Widget.aggiorna(applicationContext)
        } catch (_: Exception) {
        }
        return Result.success()
    }
}

object Lavori {
    fun pianifica(contesto: Context) {
        val vincoli = Constraints.Builder().setRequiredNetworkType(NetworkType.CONNECTED).build()
        val richiesta = PeriodicWorkRequestBuilder<ControlloWorker>(2, TimeUnit.HOURS).setConstraints(vincoli).build()
        WorkManager.getInstance(contesto).enqueueUniquePeriodicWork("controllo", ExistingPeriodicWorkPolicy.KEEP, richiesta)
    }

    fun aggiornaWidget(contesto: Context) {
        WorkManager.getInstance(contesto).enqueueUniqueWork("widget", ExistingWorkPolicy.REPLACE, OneTimeWorkRequestBuilder<WidgetWorker>().build())
    }
}

object Notifiche {
    fun creaCanali(contesto: Context) {
        val gestore = NotificationManagerCompat.from(contesto)
        listOf(
            Triple("novita", R.string.canale_novita, R.string.canale_novita_desc),
            Triple("promemoria", R.string.canale_promemoria, R.string.canale_promemoria_desc),
        ).forEach { (id, nome, descrizione) ->
            gestore.createNotificationChannel(
                NotificationChannelCompat.Builder(id, NotificationManagerCompat.IMPORTANCE_DEFAULT)
                    .setName(contesto.getString(nome))
                    .setDescription(contesto.getString(descrizione))
                    .build()
            )
        }
    }

    /** avviso: {id, canale, titolo, testo}, come lo prepara notifiche.py. */
    fun mostra(contesto: Context, avviso: JSONObject) {
        if (Build.VERSION.SDK_INT >= 33 && contesto.checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED) return
        val testo = avviso.getString("testo")
        val notifica = NotificationCompat.Builder(contesto, avviso.getString("canale"))
            .setSmallIcon(R.drawable.ic_notifica)
            .setColor(contesto.getColor(R.color.icona))
            .setContentTitle(avviso.getString("titolo"))
            .setContentText(testo.lineSequence().first())
            .setStyle(NotificationCompat.BigTextStyle().bigText(testo))
            .setContentIntent(apriApp(contesto))
            .setAutoCancel(true)
            .build()
        try {
            NotificationManagerCompat.from(contesto).notify(avviso.getString("id").hashCode(), notifica)
        } catch (_: SecurityException) {
            // permesso tolto nel frattempo
        }
    }

    fun apriApp(contesto: Context): PendingIntent = PendingIntent.getActivity(
        contesto, 0,
        Intent(contesto, MainActivity::class.java).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP),
        PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT,
    )
}
