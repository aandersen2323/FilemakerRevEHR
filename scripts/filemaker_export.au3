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
    ; Click on "Open-MAINPROEYE" in the recent files list (right side of dialog)
    ; The list is roughly in center-right of the dialog
    Local $qsPos = WinGetPos($quickStart)
    If IsArray($qsPos) Then
        MouseClick("left", $qsPos[0] + 250, $qsPos[1] + 180)
        Sleep(500)
        ; Double-click to open
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
    
    ; Click "Account Name and Password" radio button if needed
    ; Then click in Account Name field and enter credentials
    Local $loginPos = WinGetPos($loginWin)
    If IsArray($loginPos) Then
        ; Click in the Account Name field (middle of dialog)
        MouseClick("left", $loginPos[0] + ($loginPos[2] / 2), $loginPos[1] + 95)
        Sleep(200)
    EndIf
    
    ; Clear and enter username
    Send("^a")
    Sleep(100)
    Send($FM_LOGIN)
    Sleep(300)
    Send("{TAB}")
    Sleep(200)
    Send($FM_PASSWORD)
    Sleep(300)
    
    ; Click OK button
    Send("{ENTER}")
    Sleep(5000)
EndIf

; STEP 3: Main Menu - Click Manager Menu button (purple, bottom-right of menu area)
Local $mainWin = WinWait("FileMaker Pro", "", 10)
If $mainWin = 0 Then
    $mainWin = WinWait("Patients", "", 5)
EndIf

If $mainWin <> 0 Then
    WinActivate($mainWin)
    WinSetState($mainWin, "", @SW_MAXIMIZE)
    Sleep(1000)
    
    ; Manager Menu button is in the bottom-right of the teal menu area
    ; Based on screenshot: approximately at x=395, y=308 relative to menu area
    ; Menu area starts around x=45 from left edge
    ; Manager button appears to be around x=395, y=310 in the FileMaker content area
    MouseClick("left", 435, 340)
    Sleep(2000)
EndIf

; STEP 4: Manager Reports - Click Internals button (yellow, in Business Reports section)
Sleep(1000)
; Internals button is in the Business Reports section, yellow button
; Based on screenshot: around x=234, y=231
MouseClick("left", 270, 260)
Sleep(3000)

; STEP 5: Report Setup - Enter date range and click Continue
; Date field is in the center of the screen
; First click in the date field
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
; Based on screenshot: Month button around x=628, y=76
MouseClick("left", 665, 108)
Sleep(1000)

; Click View button (green, top-right)
; Based on screenshot: around x=711, y=62
MouseClick("left", 750, 95)
Sleep(3000)

; STEP 7: Save as PDF from Preview
; File menu -> Save as PDF (or Print)
Send("!f")
Sleep(500)
; Look for "Save as PDF" or use "p" for print then save as PDF
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

; Handle any confirmation dialogs
Send("{ENTER}")
Sleep(1000)

; Close FileMaker
Send("!{F4}")
Sleep(1000)
Send("n")  ; Don't save changes if prompted
Sleep(500)
