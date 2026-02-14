CHROME_BRIDGE_SCRIPT = """
on run argv
  if (count of argv) < 2 then
    return my error_envelope("applescript_error", "Missing required bridge arguments.", missing value, missing value)
  end if

  set bundleId to item 1 of argv
  set commandName to item 2 of argv
  set commandArgs to {}
  if (count of argv) > 2 then
    set commandArgs to items 3 thru -1 of argv
  end if

  try
    set payload to my dispatch_command(bundleId, commandName, commandArgs)
    return my json_obj({my json_kv("ok", my json_bool(true)), my json_kv("data", payload)})
  on error errMsg number errNum
    return my error_envelope("applescript_error", errMsg, errNum, missing value)
  end try
end run

on dispatch_command(bundleId, commandName, commandArgs)
  if commandName is "app_info" then
    return my app_info(bundleId)
  else if commandName is "list_windows" then
    return my list_windows(bundleId)
  else if commandName is "list_tabs" then
    return my list_tabs(bundleId, commandArgs)
  else if commandName is "active_tab" then
    return my active_tab(bundleId)
  else if commandName is "tab_info" then
    return my tab_info(bundleId, item 1 of commandArgs)
  else if commandName is "activate_tab" then
    return my activate_tab(bundleId, item 1 of commandArgs, item 2 of commandArgs)
  else if commandName is "reload" then
    return my reload_tab(bundleId, commandArgs)
  else if commandName is "go_back" then
    return my go_back_tab(bundleId, commandArgs)
  else if commandName is "go_forward" then
    return my go_forward_tab(bundleId, commandArgs)
  else if commandName is "stop" then
    return my stop_tab(bundleId, commandArgs)
  else if commandName is "source" then
    return my source_tab(bundleId, commandArgs)
  else if commandName is "execute_js" then
    return my execute_js(bundleId, commandArgs)
  else if commandName is "open_url" then
    return my open_url(bundleId, commandArgs)
  else if commandName is "close_tab" then
    return my close_tab(bundleId, commandArgs)
  else if commandName is "close_window" then
    return my close_window(bundleId, commandArgs)
  else if commandName is "get_window_bounds" then
    return my get_window_bounds(bundleId, commandArgs)
  else if commandName is "set_window_bounds" then
    return my set_window_bounds(bundleId, commandArgs)
  else if commandName is "bookmarks_tree" then
    return my bookmarks_tree(bundleId)
  end if

  error "Unsupported command: " & commandName number 10000
end dispatch_command

on app_info(bundleId)
  using terms from application "Google Chrome"
    tell application id bundleId
      return my json_obj({my json_kv("name", my json_string(name as text)), my json_kv("version", my json_string(version as text)), my json_kv("frontmost", my json_bool(frontmost as boolean))})
    end tell
  end using terms from
end app_info

on list_windows(bundleId)
  set entries to {}
  using terms from application "Google Chrome"
    tell application id bundleId
      set allWindows to every window
      repeat with oneWindow in allWindows
        set tabCount to count of tabs of oneWindow
        set activeTabIndexValue to active tab index of oneWindow
        set activeTabIdValue to (id of (active tab of oneWindow)) as text
        set boundsList to bounds of oneWindow
        set givenNameValue to ""
        try
          set givenNameValue to given name of oneWindow as text
        end try
        set modeValue to "normal"
        try
          set modeValue to mode of oneWindow as text
        end try
        set entry to my json_obj({my json_kv("id", my json_string((id of oneWindow) as text)), my json_kv("index", my json_num(index of oneWindow)), my json_kv("name", my json_string(name of oneWindow as text)), my json_kv("given_name", my json_string(givenNameValue)), my json_kv("bounds", my json_obj({my json_kv("left", my json_num(item 1 of boundsList)), my json_kv("top", my json_num(item 2 of boundsList)), my json_kv("right", my json_num(item 3 of boundsList)), my json_kv("bottom", my json_num(item 4 of boundsList))})), my json_kv("closeable", my json_bool(closeable of oneWindow as boolean)), my json_kv("minimizable", my json_bool(minimizable of oneWindow as boolean)), my json_kv("minimized", my json_bool(minimized of oneWindow as boolean)), my json_kv("resizable", my json_bool(resizable of oneWindow as boolean)), my json_kv("visible", my json_bool(visible of oneWindow as boolean)), my json_kv("zoomable", my json_bool(zoomable of oneWindow as boolean)), my json_kv("zoomed", my json_bool(zoomed of oneWindow as boolean)), my json_kv("mode", my json_string(modeValue)), my json_kv("active_tab_index", my json_num(activeTabIndexValue)), my json_kv("active_tab_id", my json_string(activeTabIdValue)), my json_kv("tab_count", my json_num(tabCount))})
        set end of entries to entry
      end repeat
    end tell
  end using terms from
  return my json_arr(entries)
end list_windows

on list_tabs(bundleId, commandArgs)
  set windowFilter to ""
  if (count of commandArgs) > 0 then
    set windowFilter to item 1 of commandArgs
  end if

  set entries to {}
  using terms from application "Google Chrome"
    tell application id bundleId
      set allWindows to every window
      repeat with oneWindow in allWindows
        set currentWindowId to (id of oneWindow) as text
        if windowFilter is "" or windowFilter is currentWindowId then
          set activeTabId to (id of active tab of oneWindow) as text
          set tabCount to count of tabs of oneWindow
          repeat with tabIndexValue from 1 to tabCount
            set oneTab to tab tabIndexValue of oneWindow
            set isActive to ((id of oneTab) as text is activeTabId)
            set entry to my json_obj({my json_kv("id", my json_string((id of oneTab) as text)), my json_kv("window_id", my json_string(currentWindowId)), my json_kv("index", my json_num(tabIndexValue)), my json_kv("title", my json_string(title of oneTab as text)), my json_kv("url", my json_string(URL of oneTab as text)), my json_kv("loading", my json_bool(loading of oneTab as boolean)), my json_kv("window_name", my json_string(name of oneWindow as text)), my json_kv("is_active", my json_bool(isActive))})
            set end of entries to entry
          end repeat
        end if
      end repeat
    end tell
  end using terms from
  return my json_arr(entries)
end list_tabs

on active_tab(bundleId)
  using terms from application "Google Chrome"
    tell application id bundleId
      if (count of windows) is 0 then error "No Chrome windows." number 11001
      set oneWindow to front window
      set oneTab to active tab of oneWindow
      return my json_obj({my json_kv("id", my json_string((id of oneTab) as text)), my json_kv("window_id", my json_string((id of oneWindow) as text)), my json_kv("index", my json_num(index of oneTab)), my json_kv("title", my json_string(title of oneTab as text)), my json_kv("url", my json_string(URL of oneTab as text)), my json_kv("loading", my json_bool(loading of oneTab as boolean)), my json_kv("window_name", my json_string(name of oneWindow as text)), my json_kv("is_active", my json_bool(true))})
    end tell
  end using terms from
end active_tab

on tab_info(bundleId, tabSpec)
  return my find_tab_json(bundleId, tabSpec)
end tab_info

on activate_tab(bundleId, tabSpec, focusWindow)
  using terms from application "Google Chrome"
    tell application id bundleId
      set targetInfo to my find_tab(bundleId, tabSpec)
      set oneWindow to item 1 of targetInfo
      set oneTab to item 2 of targetInfo
      set active tab index of oneWindow to index of oneTab
      if focusWindow is "1" then
        set index of oneWindow to 1
        activate
      end if
      return my json_null()
    end tell
  end using terms from
end activate_tab

on reload_tab(bundleId, commandArgs)
  set targetInfo to my resolve_target_tab(bundleId, commandArgs)
  using terms from application "Google Chrome"
    tell application id bundleId
      tell item 2 of targetInfo to reload
      return my json_null()
    end tell
  end using terms from
end reload_tab

on go_back_tab(bundleId, commandArgs)
  set targetInfo to my resolve_target_tab(bundleId, commandArgs)
  using terms from application "Google Chrome"
    tell application id bundleId
      tell item 2 of targetInfo to go back
      return my json_null()
    end tell
  end using terms from
end go_back_tab

on go_forward_tab(bundleId, commandArgs)
  set targetInfo to my resolve_target_tab(bundleId, commandArgs)
  using terms from application "Google Chrome"
    tell application id bundleId
      tell item 2 of targetInfo to go forward
      return my json_null()
    end tell
  end using terms from
end go_forward_tab

on stop_tab(bundleId, commandArgs)
  set targetInfo to my resolve_target_tab(bundleId, commandArgs)
  using terms from application "Google Chrome"
    tell application id bundleId
      tell item 2 of targetInfo to stop
      return my json_null()
    end tell
  end using terms from
end stop_tab

on source_tab(bundleId, commandArgs)
  set targetInfo to my resolve_target_tab(bundleId, commandArgs)
  using terms from application "Google Chrome"
    tell application id bundleId
      set oneTab to item 2 of targetInfo
      try
        tell oneTab to set src to source as text
      on error
        set src to execute oneTab javascript "document.documentElement.outerHTML"
        if src is missing value then set src to ""
      end try
      return my json_string(src as text)
    end tell
  end using terms from
end source_tab

on execute_js(bundleId, commandArgs)
  set jsCode to item 1 of commandArgs
  set targetArgs to {}
  if (count of commandArgs) > 1 then
    set targetArgs to {item 2 of commandArgs}
  end if
  set targetInfo to my resolve_target_tab(bundleId, targetArgs)
  using terms from application "Google Chrome"
    tell application id bundleId
      set resultValue to execute item 2 of targetInfo javascript jsCode
      if resultValue is missing value then
        return my json_string("")
      end if
      return my json_string(resultValue as text)
    end tell
  end using terms from
end execute_js

on open_url(bundleId, commandArgs)
  set targetUrl to item 1 of commandArgs
  set modeValue to item 2 of commandArgs
  set targetValue to item 3 of commandArgs
  set activateValue to item 4 of commandArgs

  using terms from application "Google Chrome"
    tell application id bundleId
      if modeValue is "tab" then
        set targetInfo to my find_tab(bundleId, targetValue)
        tell item 2 of targetInfo to set URL to targetUrl
        if activateValue is "1" then set active tab index of item 1 of targetInfo to index of item 2 of targetInfo
        return my tab_to_json(item 1 of targetInfo, item 2 of targetInfo)
      else if modeValue is "new_window" then
        if targetValue is "incognito" then
          set oneWindow to make new window with properties {mode:"incognito"}
        else
          set oneWindow to make new window
        end if
        set URL of active tab of oneWindow to targetUrl
        if activateValue is "1" then set index of oneWindow to 1
        return my tab_to_json(oneWindow, active tab of oneWindow)
      else if modeValue is "window" then
        set oneWindow to first window whose id is (targetValue as integer)
        set oneTab to make new tab at end of tabs of oneWindow with properties {URL:targetUrl}
        if activateValue is "1" then set active tab index of oneWindow to index of oneTab
        return my tab_to_json(oneWindow, oneTab)
      else
        if (count of windows) is 0 then
          set oneWindow to make new window
          set URL of active tab of oneWindow to targetUrl
          return my tab_to_json(oneWindow, active tab of oneWindow)
        end if
        set oneWindow to front window
        set oneTab to make new tab at end of tabs of oneWindow with properties {URL:targetUrl}
        if activateValue is "1" then set active tab index of oneWindow to index of oneTab
        return my tab_to_json(oneWindow, oneTab)
      end if
    end tell
  end using terms from
end open_url

on close_tab(bundleId, commandArgs)
  set targetInfo to my resolve_target_tab(bundleId, commandArgs)
  using terms from application "Google Chrome"
    tell application id bundleId
      close item 2 of targetInfo
      return my json_null()
    end tell
  end using terms from
end close_tab

on close_window(bundleId, commandArgs)
  using terms from application "Google Chrome"
    tell application id bundleId
      if (count of commandArgs) is 0 then
        if (count of windows) is 0 then error "No Chrome windows." number 11001
        close front window
        return my json_null()
      end if
      set windowId to item 1 of commandArgs
      close (first window whose id is (windowId as integer))
      return my json_null()
    end tell
  end using terms from
end close_window

on get_window_bounds(bundleId, commandArgs)
  using terms from application "Google Chrome"
    tell application id bundleId
      set oneWindow to front window
      if (count of commandArgs) > 0 then
        set oneWindow to first window whose id is (item 1 of commandArgs as integer)
      end if
      set boundsList to bounds of oneWindow
      return my json_obj({my json_kv("left", my json_num(item 1 of boundsList)), my json_kv("top", my json_num(item 2 of boundsList)), my json_kv("right", my json_num(item 3 of boundsList)), my json_kv("bottom", my json_num(item 4 of boundsList))})
    end tell
  end using terms from
end get_window_bounds

on set_window_bounds(bundleId, commandArgs)
  set maybeWindowId to item 1 of commandArgs
  set leftValue to item 2 of commandArgs as integer
  set topValue to item 3 of commandArgs as integer
  set rightValue to item 4 of commandArgs as integer
  set bottomValue to item 5 of commandArgs as integer
  using terms from application "Google Chrome"
    tell application id bundleId
      set oneWindow to front window
      if maybeWindowId is not "" then
        set oneWindow to first window whose id is (maybeWindowId as integer)
      end if
      set bounds of oneWindow to {leftValue, topValue, rightValue, bottomValue}
      return my json_null()
    end tell
  end using terms from
end set_window_bounds

on bookmarks_tree(bundleId)
  using terms from application "Google Chrome"
    tell application id bundleId
      set barFolder to bookmark folder "Bookmarks Bar"
      set otherFolder to bookmark folder "Other Bookmarks"
      return my json_obj({my json_kv("bookmarks_bar", my bookmark_folder_json(barFolder)), my json_kv("other_bookmarks", my bookmark_folder_json(otherFolder))})
    end tell
  end using terms from
end bookmarks_tree

on bookmark_folder_json(oneFolder)
  using terms from application "Google Chrome"
    set folderEntries to {}
    repeat with subFolder in bookmark folders of oneFolder
      set end of folderEntries to my bookmark_folder_json(subFolder)
    end repeat
    set itemEntries to {}
    repeat with oneItem in bookmark items of oneFolder
      set itemJson to my json_obj({my json_kv("id", my json_string((id of oneItem) as text)), my json_kv("title", my json_string(title of oneItem as text)), my json_kv("url", my json_string(URL of oneItem as text)), my json_kv("index", my json_num(index of oneItem))})
      set end of itemEntries to itemJson
    end repeat
    return my json_obj({my json_kv("id", my json_string((id of oneFolder) as text)), my json_kv("title", my json_string(title of oneFolder as text)), my json_kv("index", my json_num(index of oneFolder)), my json_kv("folders", my json_arr(folderEntries)), my json_kv("items", my json_arr(itemEntries))})
  end using terms from
end bookmark_folder_json

on resolve_target_tab(bundleId, commandArgs)
  if (count of commandArgs) is 0 then
    using terms from application "Google Chrome"
      tell application id bundleId
        if (count of windows) is 0 then error "No Chrome windows." number 11001
        set oneWindow to front window
        return {oneWindow, active tab of oneWindow}
      end tell
    end using terms from
  end if
  return my find_tab(bundleId, item 1 of commandArgs)
end resolve_target_tab

on find_tab_json(bundleId, tabSpec)
  set tabParts to my find_tab(bundleId, tabSpec)
  return my tab_to_json(item 1 of tabParts, item 2 of tabParts)
end find_tab_json

on tab_to_json(oneWindow, oneTab)
  using terms from application "Google Chrome"
    set activeTabId to ((id of (active tab of oneWindow)) as text)
    set isActive to (((id of oneTab) as text) is activeTabId)
    return my json_obj({my json_kv("id", my json_string((id of oneTab) as text)), my json_kv("window_id", my json_string((id of oneWindow) as text)), my json_kv("index", my json_num(index of oneTab)), my json_kv("title", my json_string(title of oneTab as text)), my json_kv("url", my json_string(URL of oneTab as text)), my json_kv("loading", my json_bool(loading of oneTab as boolean)), my json_kv("window_name", my json_string(name of oneWindow as text)), my json_kv("is_active", my json_bool(isActive))})
  end using terms from
end tab_to_json

on find_tab(bundleId, tabSpec)
  set AppleScript's text item delimiters to ":"
  set parts to text items of tabSpec
  set AppleScript's text item delimiters to ""

  using terms from application "Google Chrome"
    tell application id bundleId
      if (count of parts) is 2 then
        set windowId to item 1 of parts as integer
        set tabId to item 2 of parts as integer
        set oneWindow to first window whose id is windowId
        set oneTab to first tab of oneWindow whose id is tabId
        return {oneWindow, oneTab}
      end if

      set tabId to tabSpec as integer
      set matchedTabs to {}
      repeat with oneWindow in every window
        repeat with oneTab in tabs of oneWindow
          if (id of oneTab) is tabId then
            set end of matchedTabs to {oneWindow, oneTab}
          end if
        end repeat
      end repeat
      if (count of matchedTabs) is 0 then error "Tab not found." number 11003
      if (count of matchedTabs) > 1 then error "Ambiguous tab id." number 11004
      return item 1 of matchedTabs
    end tell
  end using terms from
end find_tab

on error_envelope(codeValue, messageValue, numberValue, detailsValue)
  set numberJson to my json_null()
  if numberValue is not missing value then
    set numberJson to my json_num(numberValue)
  end if
  set detailsJson to my json_null()
  if detailsValue is not missing value then
    set detailsJson to detailsValue
  end if
  return my json_obj({my json_kv("ok", my json_bool(false)), my json_kv("error", my json_obj({my json_kv("code", my json_string(codeValue)), my json_kv("message", my json_string(messageValue)), my json_kv("number", numberJson), my json_kv("details", detailsJson)}))})
end error_envelope

on replace_text(theText, searchString, replacementString)
  set oldDelims to AppleScript's text item delimiters
  set AppleScript's text item delimiters to searchString
  set textItems to every text item of theText
  set AppleScript's text item delimiters to replacementString
  set newText to textItems as text
  set AppleScript's text item delimiters to oldDelims
  return newText
end replace_text

on json_escape(rawText)
  set escapedText to my replace_text(rawText, "\\\\", "\\\\\\\\")
  set escapedText to my replace_text(escapedText, quote, (ASCII character 92) & quote)
  set escapedText to my replace_text(escapedText, return, "\\\\r")
  set escapedText to my replace_text(escapedText, linefeed, "\\\\n")
  set escapedText to my replace_text(escapedText, tab, "\\\\t")
  return escapedText
end json_escape

on json_string(rawText)
  return quote & my json_escape(rawText as text) & quote
end json_string

on json_bool(flagValue)
  if flagValue then
    return "true"
  end if
  return "false"
end json_bool

on json_num(numValue)
  return numValue as text
end json_num

on json_null()
  return "null"
end json_null

on json_kv(keyName, valueJson)
  return my json_string(keyName) & ":" & valueJson
end json_kv

on json_obj(partsList)
  if (count of partsList) is 0 then return "{}"
  set oldDelims to AppleScript's text item delimiters
  set AppleScript's text item delimiters to ","
  set resultText to "{" & (partsList as text) & "}"
  set AppleScript's text item delimiters to oldDelims
  return resultText
end json_obj

on json_arr(partsList)
  if (count of partsList) is 0 then return "[]"
  set oldDelims to AppleScript's text item delimiters
  set AppleScript's text item delimiters to ","
  set resultText to "[" & (partsList as text) & "]"
  set AppleScript's text item delimiters to oldDelims
  return resultText
end json_arr
"""
