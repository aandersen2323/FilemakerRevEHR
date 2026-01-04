#include <Date.au3>

; Configuration
Global $FM_PATH = "C:\Program Files\FileMaker\FileMaker Pro 9\FileMaker Pro.exe"
Global $FM_WINDOW = "FileMaker Pro"
Global $FM_LOGIN = "manager"
Global $FM_PASSWORD = "eynner"
Global $EXPORT_DIR = "C:\FilemakerRevEHR\exports"
Global $EXPORT_FILE = "monthly_report.pdf"
Global $W = 500
Global $WM = 1500
Global $WL = 3000

; Calculate previous month date range
Local $y = @YEAR
Local $m = @MON - 1
If $m = 0 Then
    $m = 12
    $y = $y - 1
EndIf
Local $days[13] = [0,31,28,31,30,31,30,31,31,30,31,30,31]
If $m = 2 And Mod($y, 4) = 0 Then $days[2] = 29
Local $dateRange = StringFormat("%02d/01/%04d...%02d/%02d/%04d", $m, $y, $m, $days[$m], $y)

ConsoleWrite("Date range: " & $dateRange & @CRLF)

; Create export dir if needed
If Not FileExists($EXPORT_DIR) Then DirCreate($EXPORT_DIR)

; Step 1: Launch FileMaker
If Not WinExists($FM_WINDOW) Then
    Run($FM_PATH)
    WinWaitActive($FM_WINDOW, "", 30)
EndIf
WinActivate($FM_WINDOW)
Sleep($WL)

; Step 2: Open with Shift for login
Send("+{ENTER}")
Sleep($WL)

; Step 3: Enter credentials
Send($FM_LOGIN)
Sleep(200)
Send("{TAB}")
Sleep(200)
Send($FM_PASSWORD)
Sleep(200)
Send("{ENTER}")
Sleep($WL)

; Step 4: Click Menu button (bottom-right)
Local $size = WinGetClientSize($FM_WINDOW)
MouseClick("left", $size[0] - 150, $size[1] - 100)
Sleep($WM)

; Step 5: Click lower Internals button
MouseClick("left", $size[0] / 2, $size[1] * 0.7)
Sleep($WL)

; Step 6: Enter date range
Send("^a")
Sleep(200)
Send($dateRange)
Sleep($W)
Send("{ENTER}")
Sleep($WL)

; Step 7: Select Month sort and View
MouseClick("left", $size[0] - 200, 100)
Sleep($W)
MouseClick("left", $size[0] - 100, 100)
Sleep($WL)

; Step 8: Save as PDF
Send("!f")
Sleep($W)
Send("v")
Sleep($WM)

Local $fullPath = $EXPORT_DIR & "\" & $EXPORT_FILE
Send("!n")
Sleep(200)
Send("^a")
Send($fullPath)
Sleep($W)
Send("{ENTER}")
Sleep($WM)
Send("{ENTER}")
Sleep($W)

ConsoleWrite("Done! PDF saved to: " & $fullPath & @CRLF)
