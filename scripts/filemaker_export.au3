#include <Date.au3>

; Configuration
Global $FM_PATH = "C:\Program Files (x86)\FileMaker\FileMaker Pro 9\FileMaker Pro.exe"
Global $FM_DATABASE = "C:\1Program\Open.fp7"
Global $FM_LOGIN = "manager"
Global $FM_PASSWORD = "eynner"
Global $EXPORT_DIR = "C:\FilemakerRevEHR\exports"
Global $EXPORT_FILE = "monthly_report.pdf"

; Calculate previous month
Local $y = @YEAR
Local $m = @MON - 1
If $m = 0 Then
    $m = 12
    $y = $y - 1
EndIf
Local $days[13] = [0,31,28,31,30,31,30,31,31,30,31,30,31]
If $m = 2 And Mod($y, 4) = 0 Then $days[2] = 29
Local $dateRange = StringFormat("%02d/01/%04d...%02d/%02d/%04d", $m, $y, $m, $days[$m], $y)

; Create export dir
If Not FileExists($EXPORT_DIR) Then DirCreate($EXPORT_DIR)

; Launch FileMaker with database
Run($FM_PATH & ' "' & $FM_DATABASE & '"')
If @error Then Exit
Sleep(8000)

; STEP 1: Handle Quick Start dialog if it appears
Local $quickStart = WinWait("FileMaker Quick Start", "", 5)
If $quickStart <> 0 Then
    WinActivate($quickStart)
    Sleep(500)
    Local $qsPos = WinGetPos($quickStart)
    If IsArray($qsPos) Then
        MouseClick("left", $qsPos[0] + 250, $qsPos[1] + 180, 2)
    EndIf
    Sleep(3000)
EndIf

; STEP 2: Login - password field is focused first
Local $loginWin = WinWait("Open", "", 15)
If $loginWin <> 0 Then
    WinActivate($loginWin)
    Sleep(1000)
    
    Send($FM_PASSWORD)
    Sleep(300)
    Send("{TAB}{TAB}{TAB}{TAB}{TAB}")
    Sleep(300)
    Send($FM_LOGIN)
    Sleep(300)
    Send("{ENTER}")
    ; Wait longer for files to load after login
    Sleep(10000)
EndIf

; STEP 3: After login - MAXIMIZE for consistent coordinates
Local $mainWin = WinWait("FileMaker Pro", "", 15)
If $mainWin = 0 Then
    $mainWin = WinWait("Patients", "", 10)
EndIf

If $mainWin <> 0 Then
    WinActivate($mainWin)
    WinSetState($mainWin, "", @SW_MAXIMIZE)
    Sleep(2000)
    
    ; On maximized 2560x1080, teal content area starts at approximately:
    ; x=45 (left panel), y=65 (title bar + toolbar)
    ; Manager Menu button (purple, bottom-right of teal): x=395, y=310 within teal
    ; Absolute: x=45+395=440, y=65+310=375
    MouseClick("left", 440, 375)
    Sleep(2000)
EndIf

; STEP 4: Manager Reports - Click LOWER Internals button (yellow)
Sleep(1000)
; Lower Internals in Business Reports section: approximately x=235, y=295 within teal
; Absolute: x=45+235=280, y=65+295=360
MouseClick("left", 280, 360)
Sleep(3000)

; STEP 5: Report Setup - Enter date range
; Date field approximately at x=250, y=125 within teal
; Absolute: x=45+250=295, y=65+125=190
MouseClick("left", 295, 190)
Sleep(300)
Send("^a")
Sleep(100)
Send($dateRange)
Sleep(500)

; Continue button on left side, approximately x=-20 (in left panel), y=225
; Absolute: x=25, y=65+225=290
MouseClick("left", 25, 290)
Sleep(5000)

; STEP 6: Internals Report - Click Month button, then View
; Month button in button row, approximately x=580, y=105 within teal
; Absolute: x=45+580=625, y=65+105=170
MouseClick("left", 625, 170)
Sleep(1000)

; View button approximately x=665, y=95 within teal
; Absolute: x=45+665=710, y=65+95=160
MouseClick("left", 710, 160)
Sleep(3000)

; STEP 7: Save as PDF
Send("!f")
Sleep(500)
Send("v")
Sleep(2000)

Local $fullPath = $EXPORT_DIR & "\" & $EXPORT_FILE
Send($fullPath)
Sleep(500)
Send("{ENTER}")
Sleep(2000)
Send("{ENTER}")
Sleep(1000)

; STEP 8: Snap window to left half
Send("#Left")
Sleep(500)
