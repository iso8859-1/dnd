; NSIS hooks for the Tauri installer (bundle > windows > nsis > installerHooks).

; The installer only adds and overwrites files, so cards deleted from the
; bundled data would stay behind on an update. Remove the old data folder
; before the new one is copied, but only when updating an existing install
; (the folder holds our executable) and after the running app was closed.
!macro NSIS_HOOK_PREINSTALL
  ${If} ${FileExists} "$INSTDIR\${MAINBINARYNAME}.exe"
    !insertmacro CheckIfAppIsRunning "$INSTDIR\${MAINBINARYNAME}.exe" "${PRODUCTNAME}"
    RMDir /r "$INSTDIR\data"
  ${EndIf}
!macroend
