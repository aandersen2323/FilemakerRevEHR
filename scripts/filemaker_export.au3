; ============================================================
; FileMaker Pro 9 Monthly Report Export - FULL AUTOMATION
; ============================================================
#include <Date.au3>

Global $FM_PATH = "C:\Program Files\FileMaker\FileMaker Pro 9\FileMaker Pro.exe"
Global $FM_WINDOW = "FileMaker Pro"
Global $DB_NAME = "MAINPROEYE"
Global $FM_LOGIN = "manager"
Global $FM_PASSWORD = "eynner"
Global $EXPORT_DIR = "C:\FilemakerRevEHR\exports"
Global $EXPORT_FILE = "monthly_report.pdf"
Global $LOG_FILE = "C:\FilemakerRevEHR\logs\autoit_export.log"
Global $W = 500, $WM = 1500, $WL = 3000

Func Log($m)
    FileWriteLine($LOG_FILE, @YEAR & "-" & @MON & "-" & @MDAY & " " & @HOUR & ":" & @MIN & " " & $m)
EndFunc

Func GetDateRange()
    Local $y = @YEAR, $m = @MON - 1
    If $m = 0 Then
        $m = 12
        $y -= 1
    EndIf
    Local $days[13] = [0,31,28,31,30,31,30,31,31,30,31,30,31]
    If $m = 2 And Mod($y, 4) = 0 Then $days[2] = 29
    Return StringFormat("%02d/01/%04d...%02d/%02d/%04d", $m, $y, $m, $days[$m], $y)
EndFunc

Log("=== Starting ===")
Local $dateRange = GetDateRange()
Log("Date range: " & $dateRange)

If Not FileExists($EXPORT_DIR) Then DirCreate($EXPORT_DIR)

; Step 1: Launch FileMaker
If Not WinExists($FM_WINDOW) Then
    Run($FM_PATH)
    WinWaitActive($FM_WINDOW, "", 30)
EndIf
WinActivate($FM_WINDOW)
Sleep($WL)

; Step 2: Open with login
Send("+{ENTER}")
Sleep($WL)

; Step 3: Login
Send($FM_LOGIN)
Send("{TAB}")
Send($FM_PASSWORD)
Send("{ENTER}")
Sleep($WL)

; Step 4: Click Menu
Local $size = WinGetClientSize($FM_WINDOW)
MouseClick("left", $size[0] - 150, $size[1] - 100)
Sleep($WM)

; Step 5: Click Internals
MouseClick("left", $size[0] / 2, $size[1] * 0.7)
Sleep($WL)

; Step 6: Enter dates
Send("^a")
Send($dateRange)
Send("{ENTER}")
Sleep($WL)

; Step 7: Month sort and View
MouseClick("left", $size[0] - 200, 100)
Sleep($W)
MouseClick("left", $size[0] - 100, 100)
Sleep($WL)

; Step 8: Save PDF
Send("!f")
Sleep($W)
Send("v")
Sleep($WM)
Send("!n")
Send("^a")
Send($EXPORT_DIR & "\" & $EXPORT_FILE)
Send("{ENTER}")
Sleep($WM)
Send("{ENTER}")

Log("=== Done ===")
