from vispy.color import Color
from vispy.util import set_log_level

import logging

logger = logging.getLogger(__name__)

TIMER_INTERVAL = 33
UINT64_SIZE = 8
BYTEORDER = "little"

### ROI COLOR DEFINITIONS -> START
old_verbose, _ = set_log_level("error", return_old=True)
old_verbose = logging._levelToName.get(old_verbose)

fill_alpha = 0.1
border_alpha = 1
Lime = Color("#00FF00")
Aqua = Color("#00FFFF")
Fuchsia = Color("#FF00FF")
Maroon = Color("#800000")
Brown = Color("#9A6324")
Teal = Color("#469990")
Magenta = Color("#f032e6")
Yellow = Color("#ffe119")
Pink = Color("#fabed4")
Lavender = Color("#dcbeff")
Beige = Color("#fffac8")
Apricot = Color("#ffd8b1")
Navy = Color("#000075")
Orange = Color("#f58231")
Red = Color("#e6194B")
Green = Color("#3cb44b")

TRACE_COLORS = [
    "#00FF00",
    "#00FFFF",
    "#FF00FF",
    "#800000",
    "#9A6324",
    "#469990",
    "#f032e6",
    "#ffe119",
    "#fabed4",
    "#dcbeff",
    "#fffac8",
    "#ffd8b1",
    "#000075",
    "#f58231",
    "#e6194B",
    "#3cb44b",
]


LINE_COLORS = []
# First element is border color, second element is fill color
border_1 = Lime
border_1.alpha = border_alpha
border_1 = border_1.lighter()
fill_1 = Lime
fill_1.alpha = fill_alpha
LINE_1 = [border_1, fill_1]
LINE_COLORS.append(LINE_1)

border_2 = Aqua
border_2.alpha = border_alpha
border_2 = border_2.lighter()
fill_2 = Aqua
fill_2.alpha = fill_alpha
LINE_2 = [border_2, fill_2]
LINE_COLORS.append(LINE_2)

border_3 = Fuchsia
border_3.alpha = border_alpha
border_3 = border_3.lighter()
fill_3 = Fuchsia
fill_3.alpha = fill_alpha
LINE_3 = [border_3, fill_3]
LINE_COLORS.append(LINE_3)

border_4 = Maroon
border_4.alpha = border_alpha
border_4 = border_4.lighter()
fill_4 = Maroon
fill_4.alpha = fill_alpha
LINE_4 = [border_4, fill_4]
LINE_COLORS.append(LINE_4)

border_5 = Brown
border_5.alpha = border_alpha
border_5 = border_5.lighter()
fill_5 = Brown
fill_5.alpha = fill_alpha
LINE_5 = [border_5, fill_5]
LINE_COLORS.append(LINE_5)

border_6 = Teal
border_6.alpha = border_alpha
border_6 = border_6.lighter()
fill_6 = Teal
fill_6.alpha = fill_alpha
LINE_6 = [border_6, fill_6]
LINE_COLORS.append(LINE_6)

border_7 = Yellow
border_7.alpha = border_alpha
border_7 = border_7.lighter()
fill_7 = Yellow
fill_7.alpha = fill_alpha
LINE_7 = [border_7, fill_7]
LINE_COLORS.append(LINE_7)

border_8 = Pink
border_8.alpha = border_alpha
border_8 = border_8.lighter()
fill_8 = Pink
fill_8.alpha = fill_alpha
LINE_8 = [border_8, fill_8]
LINE_COLORS.append(LINE_8)

border_9 = Lavender
border_9.alpha = border_alpha
border_9 = border_9.lighter()
fill_9 = Lavender
fill_9.alpha = fill_alpha
LINE_9 = [border_9, fill_9]
LINE_COLORS.append(LINE_9)

border_10 = Beige
border_10.alpha = border_alpha
border_10 = border_10.lighter()
fill_10 = Beige
fill_10.alpha = fill_alpha
LINE_10 = [border_10, fill_10]
LINE_COLORS.append(LINE_10)

border_11 = Navy
border_11.alpha = border_alpha
border_11 = border_11.lighter()
fill_11 = Navy
fill_11.alpha = fill_alpha
LINE_11 = [border_11, fill_11]
LINE_COLORS.append(LINE_11)

border_12 = Orange
border_12.alpha = border_alpha
border_12 = border_12.lighter()
fill_12 = Orange
fill_12.alpha = fill_alpha
LINE_12 = [border_12, fill_12]
LINE_COLORS.append(LINE_12)

border_13 = Apricot
border_13.alpha = border_alpha
border_13 = border_13.lighter()
fill_13 = Apricot
fill_13.alpha = fill_alpha
LINE_13 = [border_13, fill_13]
LINE_COLORS.append(LINE_13)

border_14 = Lavender
border_14.alpha = border_alpha
border_14 = border_14.lighter()
fill_14 = Lavender
fill_14.alpha = fill_alpha
LINE_14 = [border_14, fill_14]
LINE_COLORS.append(LINE_14)

border_15 = Red
border_15.alpha = border_alpha
border_15 = border_15.lighter()
fill_15 = Red
fill_15.alpha = fill_alpha
LINE_15 = [border_15, fill_15]
LINE_COLORS.append(LINE_15)

border_16 = Green
border_16.alpha = border_alpha
border_16 = border_16.lighter()
fill_16 = Green
fill_16.alpha = fill_alpha
LINE_16 = [border_16, fill_16]
LINE_COLORS.append(LINE_16)

set_log_level(old_verbose)
### ROI COLOR DEFINITIONS -> END
