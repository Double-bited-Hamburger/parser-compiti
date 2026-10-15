package it.registro.app

import android.content.Context
import android.graphics.Bitmap
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.graphics.PorterDuff
import android.graphics.PorterDuffXfermode
import android.graphics.Typeface
import kotlin.math.ceil
import kotlin.math.roundToInt

/**
 * I numeri dei widget col tema Ultra, come le scritte della lattina bianca: neri, stretti e pesanti, inclinati,
 * con graffi e puntini «strappati» via. I widget non possono usare font propri: la scritta diventa un'immagine.
 */
object Lattina {
    fun numero(testo: String, contesto: Context, altezzaDp: Float = 48f): Bitmap {
        val densita = contesto.resources.displayMetrics.density
        val pennello = Paint(Paint.ANTI_ALIAS_FLAG).apply {
            typeface = Typeface.create("sans-serif-condensed", Typeface.BOLD)
            textSize = altezzaDp * densita * 1.15f
            textSkewX = -0.14f
            color = Color.parseColor("#111111")
            isFakeBoldText = true
        }
        val metriche = pennello.fontMetrics
        val larghezza = ceil(pennello.measureText(testo) + pennello.textSize * 0.2f).toInt().coerceAtLeast(1)
        val altezza = ceil(metriche.descent - metriche.ascent).toInt().coerceAtLeast(1)
        val immagine = Bitmap.createBitmap(larghezza, altezza, Bitmap.Config.ARGB_8888)
        val tela = Canvas(immagine)
        tela.drawText(testo, pennello.textSize * 0.06f, -metriche.ascent, pennello)

        // L'usura: buchini e due graffi sottili tolti dalla scritta, sempre uguali per lo stesso testo.
        val gomma = Paint(Paint.ANTI_ALIAS_FLAG).apply { xfermode = PorterDuffXfermode(PorterDuff.Mode.CLEAR) }
        var seme = testo.hashCode().toLong() and 0xffff
        fun caso(): Float { seme = (seme * 9301 + 49297) % 233280; return seme / 233280f }
        repeat((larghezza * altezza / (90 * densita * densita)).roundToInt().coerceIn(6, 60)) {
            tela.drawCircle(caso() * larghezza, caso() * altezza, (0.4f + caso() * 1.1f) * densita, gomma)
        }
        gomma.strokeWidth = 0.8f * densita
        tela.drawLine(0f, altezza * 0.34f, larghezza.toFloat(), altezza * 0.38f, gomma)
        tela.drawLine(0f, altezza * 0.71f, larghezza.toFloat(), altezza * 0.66f, gomma)
        return immagine
    }
}
