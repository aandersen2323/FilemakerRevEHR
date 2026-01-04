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
        ; Double-click on "Open-MAINPROEYE" in recent files list
        MouseClick("left", $qsPos[0] + 250, $qsPos[1] + 180, 2)
    EndIf
    Sleep(3000)
EndIf

; STEP 2: Handle Login dialog
Local $loginWin = WinWait("Open", "Account", 10)
If $loginWin = 0 Then
    $loginWin = WinWait("Open", "Password", 10)
EndIf

If $loginWin <> 0 Then
    WinActivate($loginWin)
    Sleep(500)
    
    Local $loginPos = WinGetPos($loginWin)
    If IsArray($loginPos) Then
        ; Click in the Account Name field
        MouseClick("left", $loginPos[0] + ($loginPos[2] / 2), $loginPos[1] + 95)
        Sleep(200)
    EndIf
    
    Send("^a")
    Sleep(100)
    Send($FM_LOGIN)
    Sleep(300)
    Send("{TAB}")
    Sleep(200)
    Send($FM_PASSWORD)
    Sleep(300)
    Send("{ENTER}")
    Sleep(5000)
EndIf

; STEP 3: Main Menu - Click REPORTS Menu button (GREEN, in Reports section)
; NOT Manager Menu - it's the Reports Menu button
Local $mainWin = WinWait("FileMaker Pro", "", 10)
If $mainWin = 0 Then
    $mainWin = WinWait("Patients", "", 5)
EndIf

If $mainWin <> 0 Then
    WinActivate($mainWin)
    WinSetState($mainWin, "", @SW_MAXIMIZE)
    Sleep(1000)
    
    ; Reports Menu button is green, in the Reports section (middle-left area)
    ; From screenshot: Reports section is below Lookups, Menu button around x=207, y=192
    MouseClick("left", 245, 225)
    Sleep(2000)
EndIf

; STEP 4: Business Reports screen - Click LOWER Internals button (yellow)
; There are two Internals buttons - we want the LOWER one
Sleep(1000)
; Lower Internals button is below the upper one, around y=231
MouseClick("left", 270, 265)
Sleep(3000)

; STEP 5: Report Setup - Enter date range and click Continue
MouseClick("left", 290, 155)
Sleep(300)
Send("^a")
Sleep(100)
Send($dateRange)
Sleep(500)

; Click Continue button (left side)
MouseClick("left", 50, 258)
Sleep(5000)

; STEP 6: Internals Report - Click Month sort button, then View
; Month button is in the top-right button group
MouseClick("left", 665, 108)
Sleep(1000)

; Click View button (green, top-right)
MouseClick("left", 750, 95)
Sleep(3000)

; STEP 7: Save as PDF from Preview
Send("!f")
Sleep(500)
Send("v")
Sleep(2000)

; Save dialog - enter filename
Local $saveWin = WinWait("Save", "", 5)
If $saveWin <> 0 Then
    WinActivate($saveWin)
    Sleep(500)
EndIf

Local $fullPath = $EXPORT_DIR & "\" & $EXPORT_FILE
Send($fullPath)
Sleep(500)
Send("{ENTER}")
Sleep(2000)
Send("{ENTER}")
Sleep(1000)

; Close FileMaker
Send("!{F4}")
Sleep(1000)
Send("n")
Sleep(500)
