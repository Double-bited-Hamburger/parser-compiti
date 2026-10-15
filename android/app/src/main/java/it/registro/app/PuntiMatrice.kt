package it.registro.app

import android.content.Context
import android.graphics.Bitmap
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import java.text.Normalizer
import kotlin.math.roundToInt

/**
 * Scritte a punti, come i display a matrice dei telefoni Nothing: ogni carattere è una griglia 5×7 di puntini.
 * Il disegno è bianco (acceso) e bianco quasi trasparente (spento): il colore vero lo dà il tint dell'ImageView
 * nel layout del widget, che il launcher risolve da sé in tema chiaro o scuro.
 */
object PuntiMatrice {
    private const val SPENTO = 30 // trasparenza dei puntini spenti, su 255

    // Righe dall'alto in basso; '#' = puntino acceso. I segni stretti (: . !) occupano meno colonne.
    private val CARATTERI: Map<Char, List<String>> = mapOf(
        '0' to " ### |#   #|#  ##|# # #|##  #|#   #| ### ",
        '1' to "  #  | ##  |  #  |  #  |  #  |  #  | ### ",
        '2' to " ### |#   #|    #|   # |  #  | #   |#####",
        '3' to "#####|   # |  #  |   # |    #|#   #| ### ",
        '4' to "   # |  ## | # # |#  # |#####|   # |   # ",
        '5' to "#####|#    |#### |    #|    #|#   #| ### ",
        '6' to "  ## | #   |#    |#### |#   #|#   #| ### ",
        '7' to "#####|    #|   # |  #  | #   | #   | #   ",
        '8' to " ### |#   #|#   #| ### |#   #|#   #| ### ",
        '9' to " ### |#   #|#   #| ####|    #|   # | ##  ",
        'A' to " ### |#   #|#   #|#####|#   #|#   #|#   #",
        'B' to "#### |#   #|#   #|#### |#   #|#   #|#### ",
        'C' to " ### |#   #|#    |#    |#    |#   #| ### ",
        'D' to "###  |#  # |#   #|#   #|#   #|#  # |###  ",
        'E' to "#####|#    |#    |#### |#    |#    |#####",
        'F' to "#####|#    |#    |#### |#    |#    |#    ",
        'G' to " ### |#   #|#    |# ###|#   #|#   #| ####",
        'H' to "#   #|#   #|#   #|#####|#   #|#   #|#   #",
        'I' to " ### |  #  |  #  |  #  |  #  |  #  | ### ",
        'J' to "  ###|   # |   # |   # |   # |#  # | ##  ",
        'K' to "#   #|#  # |# #  |##   |# #  |#  # |#   #",
        'L' to "#    |#    |#    |#    |#    |#    |#####",
        'M' to "#   #|## ##|# # #|# # #|#   #|#   #|#   #",
        'N' to "#   #|#   #|##  #|# # #|#  ##|#   #|#   #",
        'O' to " ### |#   #|#   #|#   #|#   #|#   #| ### ",
        'P' to "#### |#   #|#   #|#### |#    |#    |#    ",
        'Q' to " ### |#   #|#   #|#   #|# # #|#  # | ## #",
        'R' to "#### |#   #|#   #|#### |# #  |#  # |#   #",
        'S' to " ####|#    |#    | ### |    #|    #|#### ",
        'T' to "#####|  #  |  #  |  #  |  #  |  #  |  #  ",
        'U' to "#   #|#   #|#   #|#   #|#   #|#   #| ### ",
        'V' to "#   #|#   #|#   #|#   #|#   #| # # |  #  ",
        'W' to "#   #|#   #|#   #|# # #|# # #|# # #| # # ",
        'X' to "#   #|#   #| # # |  #  | # # |#   #|#   #",
        'Y' to "#   #|#   #| # # |  #  |  #  |  #  |  #  ",
        'Z' to "#####|    #|   # |  #  | #   |#    |#####",
        '-' to "     |     |     | ### |     |     |     ",
        '+' to "     |  #  |  #  |#####|  #  |  #  |     ",
        '/' to "    #|    #|   # |  #  | #   |#    |#    ",
        '?' to " ### |#   #|    #|   # |  #  |     |  #  ",
        ':' to " | |#| | |#| ",
        '.' to " | | | | | |#",
        '!' to "#|#|#|#|#| |#",
        ' ' to "   |   |   |   |   |   |   ",
    ).mapValues { it.value.split('|') }

    /** La scritta come immagine; il passo tra un puntino e l'altro è di 6dp. */
    fun disegna(testo: String, contesto: Context): Bitmap {
        val passo = (6 * contesto.resources.displayMetrics.density).roundToInt().coerceAtLeast(4)
        val pulito = Normalizer.normalize(testo.uppercase(), Normalizer.Form.NFD).replace(Regex("\\p{M}"), "")
        val glifi = pulito.map { CARATTERI[it] ?: CARATTERI.getValue('?') }.ifEmpty { listOf(CARATTERI.getValue(' ')) }
        val colonne = glifi.sumOf { it[0].length } + glifi.size - 1 // una colonna vuota tra due caratteri
        val immagine = Bitmap.createBitmap(colonne * passo, 7 * passo, Bitmap.Config.ARGB_8888)
        val tela = Canvas(immagine)
        val pennello = Paint(Paint.ANTI_ALIAS_FLAG).apply { color = Color.WHITE }
        val raggio = passo * 0.4f
        var x0 = 0
        glifi.forEachIndexed { i, righe ->
            val larghezza = righe[0].length + if (i < glifi.size - 1) 1 else 0
            for (riga in 0 until 7) for (colonna in 0 until larghezza) {
                val acceso = colonna < righe[riga].length && righe[riga][colonna] == '#'
                pennello.alpha = if (acceso) 255 else SPENTO
                tela.drawCircle((x0 + colonna + 0.5f) * passo, (riga + 0.5f) * passo, raggio, pennello)
            }
            x0 += larghezza
        }
        return immagine
    }
}
