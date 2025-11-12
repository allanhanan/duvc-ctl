# test-duvc-cli.ps1
# Comprehensive capability-aware test script for duvc-cli
# Tests ALL CLI features based on actual device capabilities
# Usage: .\test-duvc-cli.ps1 [-CLI <path>] [-NoDevice] [-Verbose]

param(
    [string]$CLI = ".\duvc-cli.exe",
    [switch]$NoDevice,
    [switch]$Verbose
)

$ErrorActionPreference = "Continue"
$script:PassCount = 0
$script:FailCount = 0
$script:SkipCount = 0
$script:TestResults = @()
$script:DeviceCaps = $null

function Write-TestHeader {
    param([string]$Message)
    Write-Host "`n===============================================================================" -ForegroundColor Cyan
    Write-Host "  $Message" -ForegroundColor Cyan
    Write-Host "===============================================================================" -ForegroundColor Cyan
}

function Write-TestSection {
    param([string]$Message)
    Write-Host "`n>> $Message" -ForegroundColor Yellow
}

function Test-Command {
    param(
        [string]$Name,
        [string]$Command,
        [string]$ExpectedPattern = "",
        [bool]$ShouldSucceed = $true,
        [bool]$SkipIfNoDevice = $false
    )
    
    if ($SkipIfNoDevice -and $script:NoDevice) {
        Write-Host "  [SKIP] $Name" -ForegroundColor DarkGray
        $script:SkipCount++
        $script:TestResults += [PSCustomObject]@{Test=$Name; Status="SKIP"; Reason="No device"}
        return
    }
    
    if ($Verbose) {
        Write-Host "  [TEST] $Name" -ForegroundColor Blue
        Write-Host "         $CLI $Command" -ForegroundColor DarkGray
    }
    
    try {
        $output = & $CLI $Command.Split(' ') 2>&1 | Out-String
        $exitCode = $LASTEXITCODE
        
        $success = $false
        if ($ShouldSucceed) {
            $success = ($exitCode -eq 0)
            if ($ExpectedPattern -and $success) {
                $success = ($output -match $ExpectedPattern)
            }
        } else {
            $success = ($exitCode -ne 0)
        }
        
        if ($success) {
            Write-Host "  [PASS] $Name" -ForegroundColor Green
            $script:PassCount++
            $script:TestResults += [PSCustomObject]@{Test=$Name; Status="PASS"; Command=$Command}
        } else {
            Write-Host "  [FAIL] $Name" -ForegroundColor Red
            if ($Verbose) {
                Write-Host "         Exit: $exitCode" -ForegroundColor DarkGray
                Write-Host "         $($output.Substring(0, [Math]::Min(120, $output.Length)))" -ForegroundColor DarkGray
            }
            $script:FailCount++
            $script:TestResults += [PSCustomObject]@{Test=$Name; Status="FAIL"; Command=$Command; Exit=$exitCode}
        }
    } catch {
        Write-Host "  [ERROR] $Name - $_" -ForegroundColor Red
        $script:FailCount++
        $script:TestResults += [PSCustomObject]@{Test=$Name; Status="ERROR"; Error=$_.Exception.Message}
    }
}

function Get-DeviceCapabilities {
    param([int]$Index)
    
    Write-Host "`nQuerying device capabilities..." -ForegroundColor Cyan
    
    try {
        $capsJson = & $CLI "-j" "capabilities" "$Index" 2>&1 | Out-String
        if ($LASTEXITCODE -ne 0) {
            Write-Host "Failed to query capabilities (exit $LASTEXITCODE)" -ForegroundColor Red
            return $null
        }
        
        $caps = $capsJson | ConvertFrom-Json
        $result = @{CameraProps=@{}; VideoProps=@{}}
        
        foreach ($prop in $caps.capabilities) {
            $info = @{
                Min = $prop.min
                Max = $prop.max
                Step = if($prop.step -eq 0){1}else{$prop.step}
                Default = $prop.default
                Current = $prop.current
                Mode = $prop.mode
            }
            
            if ($prop.domain -eq "cam") {
                $result.CameraProps[$prop.property] = $info
            } elseif ($prop.domain -eq "vid") {
                $result.VideoProps[$prop.property] = $info
            }
        }
        
        Write-Host "Camera properties: $($result.CameraProps.Count)" -ForegroundColor Green
        Write-Host "Video properties: $($result.VideoProps.Count)" -ForegroundColor Green
        
        if ($result.CameraProps.Count -gt 0) {
            Write-Host "  Cam: $($result.CameraProps.Keys -join ', ')" -ForegroundColor DarkGray
        }
        if ($result.VideoProps.Count -gt 0) {
            Write-Host "  Vid: $($result.VideoProps.Keys -join ', ')" -ForegroundColor DarkGray
        }
        
        return $result
    } catch {
        Write-Host "Error parsing capabilities: $_" -ForegroundColor Yellow
        return $null
    }
}

function Get-ValidTestValue {
    param([int]$Min, [int]$Max, [int]$Step, [int]$Current)
    
    $step = if($Step -eq 0){1}else{$Step}
    $target = $Current + $step
    
    if ($target -gt $Max) { $target = $Min }
    if ($target -lt $Min) { $target = $Min }
    
    # Align to step
    if ($step -gt 1) {
        $offset = ($target - $Min) % $step
        if ($offset -ne 0) {
            $target = $target - $offset
        }
    }
    
    return [Math]::Max($Min, [Math]::Min($Max, $target))
}

# ============================================================================
# MAIN
# ============================================================================

Write-TestHeader "DUVC-CLI Comprehensive Test Suite"

if (-not (Test-Path $CLI)) {
    Write-Host "ERROR: CLI not found at $CLI" -ForegroundColor Red
    exit 1
}

Write-Host "CLI: $CLI"
Write-Host "Mode: $(if($NoDevice){'NoDevice'}else{'With Device'})"
Write-Host "Verbose: $Verbose"

# Check for devices
$devList = & $CLI "list" 2>&1 | Out-String
$hasDevice = ($devList -match "\[0\]")

if (-not $NoDevice -and -not $hasDevice) {
    Write-Host "`nWARNING: No devices found. Switching to NoDevice mode" -ForegroundColor Yellow
    $script:NoDevice = $true
}

Write-Host "Device present: $hasDevice"

# ============================================================================
# SECTION 1: GLOBAL FLAGS & BASIC COMMANDS
# ============================================================================

Write-TestSection "Global Flags & Basic Commands"

Test-Command "Help (--help)" "--help" -Pattern "duvc-cli"
Test-Command "Help (-h)" "-h" -Pattern "duvc-cli"
Test-Command "List devices" "list" -Pattern "Devices:"
Test-Command "List detailed" "list --detailed"
Test-Command "List detailed (short)" "list -d"
Test-Command "Verbose flag (-v)" "-v list" -Pattern "Devices:"
Test-Command "Quiet flag (-q)" "-q list"
Test-Command "JSON flag (-j)" "-j list" -Pattern '\{"devices":\['
Test-Command "Combined flags" "-v -j list" -Pattern '\{'

# ============================================================================
# SECTION 2: DEVICE STATUS
# ============================================================================

if (-not $script:NoDevice) {
    Write-TestSection "Device Status"
    
    Test-Command "Status" "status 0" -Pattern "CONNECTED|DISCONNECTED" -SkipIfNoDevice $true
    Test-Command "Status JSON" "-j status 0" -Pattern '\{"index":0' -SkipIfNoDevice $true
}

# ============================================================================
# SECTION 3: CAPABILITIES QUERY
# ============================================================================

if (-not $script:NoDevice) {
    Write-TestSection "Capabilities Query"
    
    Test-Command "Capabilities" "capabilities 0" -Pattern "CAM|VID|Capabilities:" -SkipIfNoDevice $true
    Test-Command "Capabilities JSON" "-j capabilities 0" -Pattern '\{"device":0,"capabilities":\[' -SkipIfNoDevice $true
    Test-Command "Capabilities verbose" "-v capabilities 0" -SkipIfNoDevice $true
    
    # Load capabilities for intelligent testing
    $script:DeviceCaps = Get-DeviceCapabilities -Index 0
}

# ============================================================================
# SECTION 4: PROPERTY GET OPERATIONS (CAPABILITY-AWARE)
# ============================================================================

if (-not $script:NoDevice -and $script:DeviceCaps) {
    Write-TestSection "Property Get Operations (Capability-Aware)"
    
    # Camera properties
    if ($script:DeviceCaps.CameraProps.Count -gt 0) {
        foreach ($prop in $script:DeviceCaps.CameraProps.Keys) {
            Test-Command "Get cam.$prop" "get 0 cam $prop" -Pattern "$prop=" -SkipIfNoDevice $true
        }
        
        # Batch get
        $props = ($script:DeviceCaps.CameraProps.Keys | Select-Object -First 3) -join ","
        if ($props -match ",") {
            Test-Command "Batch get cam ($props)" "get 0 cam $props" -SkipIfNoDevice $true
        }
    } else {
        Write-Host "  [INFO] No camera properties supported" -ForegroundColor DarkGray
        $script:SkipCount += 5
    }
    
    # Video properties
    if ($script:DeviceCaps.VideoProps.Count -gt 0) {
        foreach ($prop in $script:DeviceCaps.VideoProps.Keys) {
            Test-Command "Get vid.$prop" "get 0 vid $prop" -Pattern "$prop=" -SkipIfNoDevice $true
        }
        
        # Batch get
        $props = ($script:DeviceCaps.VideoProps.Keys | Select-Object -First 3) -join ","
        if ($props -match ",") {
            Test-Command "Batch get vid ($props)" "get 0 vid $props" -SkipIfNoDevice $true
        }
        
        # JSON output
        $firstProp = $script:DeviceCaps.VideoProps.Keys | Select-Object -First 1
        Test-Command "Get JSON" "-j get 0 vid $firstProp" -Pattern '\{"device":0' -SkipIfNoDevice $true
    } else {
        Write-Host "  [INFO] No video properties supported" -ForegroundColor DarkGray
        $script:SkipCount += 5
    }
}

# ============================================================================
# SECTION 5: PROPERTY SET OPERATIONS (CAPABILITY-AWARE)
# ============================================================================

if (-not $script:NoDevice -and $script:DeviceCaps) {
    Write-TestSection "Property Set Operations (Capability-Aware)"
    
    # Camera properties
    if ($script:DeviceCaps.CameraProps.Count -gt 0) {
        foreach ($prop in $script:DeviceCaps.CameraProps.Keys) {
            $info = $script:DeviceCaps.CameraProps[$prop]
            $testVal = Get-ValidTestValue -Min $info.Min -Max $info.Max -Step $info.Step -Current $info.Current
            
            Test-Command "Set cam.$prop=$testVal" "set 0 cam $prop $testVal" -Pattern "OK" -SkipIfNoDevice $true
            
            # Verify
            $verify = & $CLI "get" "0" "cam" "$prop" 2>&1 | Out-String
            if ($verify -match "$prop=$testVal") {
                Write-Host "  [PASS] Verify cam.$prop=$testVal" -ForegroundColor Green
                $script:PassCount++
            } else {
                Write-Host "  [FAIL] Verify cam.$prop=$testVal" -ForegroundColor Red
                if ($Verbose) { Write-Host "    Got: $verify" -ForegroundColor DarkGray }
                $script:FailCount++
            }
        }
        
        # Batch set
        $setBatch = @()
        $i = 0
        foreach ($prop in $script:DeviceCaps.CameraProps.Keys) {
            if ($i -ge 2) { break }
            $info = $script:DeviceCaps.CameraProps[$prop]
            $val = Get-ValidTestValue -Min $info.Min -Max $info.Max -Step $info.Step -Current $info.Current
            $setBatch += "$prop=$val"
            $i++
        }
        if ($setBatch.Count -ge 2) {
            Test-Command "Batch set cam" "set 0 cam $($setBatch -join ',')" -Pattern "OK" -SkipIfNoDevice $true
        }
    }
    
    # Video properties
    if ($script:DeviceCaps.VideoProps.Count -gt 0) {
        foreach ($prop in $script:DeviceCaps.VideoProps.Keys) {
            $info = $script:DeviceCaps.VideoProps[$prop]
            $testVal = Get-ValidTestValue -Min $info.Min -Max $info.Max -Step $info.Step -Current $info.Current
            
            Test-Command "Set vid.$prop=$testVal" "set 0 vid $prop $testVal" -Pattern "OK" -SkipIfNoDevice $true
            
            # Verify
            $verify = & $CLI "get" "0" "vid" "$prop" 2>&1 | Out-String
            if ($verify -match "$prop=$testVal") {
                Write-Host "  [PASS] Verify vid.$prop=$testVal" -ForegroundColor Green
                $script:PassCount++
            } else {
                Write-Host "  [FAIL] Verify vid.$prop=$testVal" -ForegroundColor Red
                if ($Verbose) { Write-Host "    Got: $verify" -ForegroundColor DarkGray }
                $script:FailCount++
            }
        }
        
        # Batch set with mode
        $prop1 = $script:DeviceCaps.VideoProps.Keys | Select-Object -First 1
        if ($prop1) {
            $info1 = $script:DeviceCaps.VideoProps[$prop1]
            $val1 = Get-ValidTestValue -Min $info1.Min -Max $info1.Max -Step $info1.Step -Current $info1.Current
            Test-Command "Set with mode" "set 0 vid $prop1=$val1:manual" -Pattern "OK" -SkipIfNoDevice $true
        }
    }
}

# ============================================================================
# SECTION 6: MODE-ONLY SET OPERATIONS
# ============================================================================

if (-not $script:NoDevice -and $script:DeviceCaps) {
    Write-TestSection "Mode-Only Set Operations"
    
    $testProp = $script:DeviceCaps.CameraProps.Keys | Select-Object -First 1
    if (-not $testProp) {
        $testProp = $script:DeviceCaps.VideoProps.Keys | Select-Object -First 1
        $domain = "vid"
    } else {
        $domain = "cam"
    }
    
    if ($testProp) {
        Test-Command "Set $testProp to auto" "set 0 $domain $testProp auto" -Pattern "OK" -SkipIfNoDevice $true
        Test-Command "Set $testProp to manual" "set 0 $domain $testProp manual" -Pattern "OK" -SkipIfNoDevice $true
    }
}

# ============================================================================
# SECTION 7: RELATIVE VALUE OPERATIONS (WITH --relative FLAG)
# ============================================================================

if (-not $script:NoDevice -and $script:DeviceCaps) {
    Write-TestSection "Relative Value Operations (with --relative flag)"
    
    # Test relative operations on camera properties
    if ($script:DeviceCaps.CameraProps.Count -gt 0) {
        $testProp = $script:DeviceCaps.CameraProps.Keys | Select-Object -First 1
        $info = $script:DeviceCaps.CameraProps[$testProp]
        
        # Get current value
        $currentOutput = & $CLI "get" "0" "cam" "$testProp" 2>&1 | Out-String
        if ($currentOutput -match "$testProp=(-?\d+)") {
            $currentValue = [int]$Matches[1]
            
            # Calculate safe delta (within range)
            $delta = $info.Step
            if ($delta -eq 0) { $delta = 1 }
            
            # Test relative increase
            if ($currentValue + $delta -le $info.Max) {
                Test-Command "Relative cam.$testProp +$delta" "set --relative 0 cam $testProp +$delta" -Pattern "OK" -SkipIfNoDevice $true
                
                # Verify the change
                $newOutput = & $CLI "get" "0" "cam" "$testProp" 2>&1 | Out-String
                if ($newOutput -match "$testProp=(-?\d+)") {
                    $newValue = [int]$Matches[1]
                    $expected = $currentValue + $delta
                    if ($newValue -eq $expected) {
                        Write-Host "  [PASS] Verify relative increase: $currentValue -> $newValue" -ForegroundColor Green
                        $script:PassCount++
                    } else {
                        Write-Host "  [FAIL] Verify relative increase: expected $expected, got $newValue" -ForegroundColor Red
                        $script:FailCount++
                    }
                }
                $currentValue = $newValue
            }
            
            # Test relative decrease
            if ($currentValue - $delta -ge $info.Min) {
                Test-Command "Relative cam.$testProp -$delta" "set -r 0 cam $testProp -$delta" -Pattern "OK" -SkipIfNoDevice $true
                
                # Verify the change
                $newOutput = & $CLI "get" "0" "cam" "$testProp" 2>&1 | Out-String
                if ($newOutput -match "$testProp=(-?\d+)") {
                    $newValue = [int]$Matches[1]
                    $expected = $currentValue - $delta
                    if ($newValue -eq $expected) {
                        Write-Host "  [PASS] Verify relative decrease: $currentValue -> $newValue" -ForegroundColor Green
                        $script:PassCount++
                    } else {
                        Write-Host "  [FAIL] Verify relative decrease: expected $expected, got $newValue" -ForegroundColor Red
                        $script:FailCount++
                    }
                }
            }
        }
    }
    
    # Test relative operations on video properties
    if ($script:DeviceCaps.VideoProps.Count -gt 0) {
        $testProp = $script:DeviceCaps.VideoProps.Keys | Select-Object -First 1
        $info = $script:DeviceCaps.VideoProps[$testProp]
        
        # Get current value
        $currentOutput = & $CLI "get" "0" "vid" "$testProp" 2>&1 | Out-String
        if ($currentOutput -match "$testProp=(-?\d+)") {
            $currentValue = [int]$Matches[1]
            
            # Calculate safe delta
            $delta = $info.Step
            if ($delta -eq 0) { $delta = 1 }
            
            # Test relative increase
            if ($currentValue + $delta -le $info.Max) {
                Test-Command "Relative vid.$testProp +$delta" "set --relative 0 vid $testProp +$delta" -Pattern "OK" -SkipIfNoDevice $true
                
                # Verify the change
                $newOutput = & $CLI "get" "0" "vid" "$testProp" 2>&1 | Out-String
                if ($newOutput -match "$testProp=(-?\d+)") {
                    $newValue = [int]$Matches[1]
                    $expected = $currentValue + $delta
                    if ($newValue -eq $expected) {
                        Write-Host "  [PASS] Verify relative increase: $currentValue -> $newValue" -ForegroundColor Green
                        $script:PassCount++
                    } else {
                        Write-Host "  [FAIL] Verify relative increase: expected $expected, got $newValue" -ForegroundColor Red
                        $script:FailCount++
                    }
                }
            }
        }
    }
}


# ============================================================================
# SECTION 8: RANGE QUERIES
# ============================================================================

if (-not $script:NoDevice -and $script:DeviceCaps) {
    Write-TestSection "Range Queries"
    
    # Individual properties
    if ($script:DeviceCaps.CameraProps.Count -gt 0) {
        $prop = $script:DeviceCaps.CameraProps.Keys | Select-Object -First 1
        Test-Command "Range cam.$prop" "range 0 cam $prop" -Pattern "\[.*,.*\]" -SkipIfNoDevice $true
    }
    
    if ($script:DeviceCaps.VideoProps.Count -gt 0) {
        $prop = $script:DeviceCaps.VideoProps.Keys | Select-Object -First 1
        Test-Command "Range vid.$prop" "range 0 vid $prop" -Pattern "\[.*,.*\]" -SkipIfNoDevice $true
    }
    
    # Batch ranges
    if ($script:DeviceCaps.CameraProps.Count -ge 2) {
        $props = ($script:DeviceCaps.CameraProps.Keys | Select-Object -First 2) -join ","
        Test-Command "Range cam multiple" "range 0 cam $props" -SkipIfNoDevice $true
    }
    
    # All ranges
    Test-Command "Range cam all" "range 0 cam all" -SkipIfNoDevice $true
    Test-Command "Range vid all" "range 0 vid all" -SkipIfNoDevice $true
    Test-Command "Range all domains" "range 0 all all" -SkipIfNoDevice $true
    Test-Command "Range JSON" "-j range 0 vid all" -Pattern '\{"device":0,"ranges":\[' -SkipIfNoDevice $true
}

# ============================================================================
# SECTION 9: RESET OPERATIONS
# ============================================================================

if (-not $script:NoDevice -and $script:DeviceCaps) {
    Write-TestSection "Reset Operations"
    
    # Reset individual properties
    if ($script:DeviceCaps.CameraProps.Count -gt 0) {
        $prop = $script:DeviceCaps.CameraProps.Keys | Select-Object -First 1
        Test-Command "Reset cam.$prop" "reset 0 cam $prop" -Pattern "Reset" -SkipIfNoDevice $true
    }
    
    if ($script:DeviceCaps.VideoProps.Count -gt 0) {
        $prop = $script:DeviceCaps.VideoProps.Keys | Select-Object -First 1
        Test-Command "Reset vid.$prop" "reset 0 vid $prop" -Pattern "Reset" -SkipIfNoDevice $true
    }
    
    # Reset multiple
    if ($script:DeviceCaps.VideoProps.Count -ge 2) {
        $props = ($script:DeviceCaps.VideoProps.Keys | Select-Object -First 2) -join ","
        Test-Command "Reset vid multiple" "reset 0 vid $props" -Pattern "Reset" -SkipIfNoDevice $true
    }
    
    # Reset all
    Test-Command "Reset cam all" "reset 0 cam all" -Pattern "Reset" -SkipIfNoDevice $true
    Test-Command "Reset vid all" "reset 0 vid all" -Pattern "Reset" -SkipIfNoDevice $true
    Test-Command "Reset all domains" "reset 0 all" -Pattern "Reset" -SkipIfNoDevice $true
}

# ============================================================================
# SECTION 10: SNAPSHOT OPERATIONS
# ============================================================================

if (-not $script:NoDevice) {
    Write-TestSection "Snapshot Operations"
    
    Test-Command "Snapshot text" "snapshot 0" -Pattern "cam\.|vid\." -SkipIfNoDevice $true
    Test-Command "Snapshot JSON" "-j snapshot 0" -Pattern '\{"device":0' -SkipIfNoDevice $true
    
    # Snapshot to file
    $tmpFile = "$env:TEMP\duvc-snap-$([guid]::NewGuid().ToString().Substring(0,8)).txt"
    & $CLI "snapshot" "0" "-o" "$tmpFile" 2>&1 | Out-Null
    
    if ((Test-Path $tmpFile) -and ((Get-Content $tmpFile -Raw).Length -gt 10)) {
        Write-Host "  [PASS] Snapshot to file" -ForegroundColor Green
        $script:PassCount++
        $script:TestResults += [PSCustomObject]@{Test="Snapshot to file"; Status="PASS"}
    } else {
        Write-Host "  [FAIL] Snapshot to file" -ForegroundColor Red
        $script:FailCount++
        $script:TestResults += [PSCustomObject]@{Test="Snapshot to file"; Status="FAIL"}
    }
    
    Remove-Item $tmpFile -ErrorAction SilentlyContinue
    
    # JSON snapshot to file
    $tmpFile2 = "$env:TEMP\duvc-snap-$([guid]::NewGuid().ToString().Substring(0,8)).json"
    & $CLI "-j" "snapshot" "0" "-o" "$tmpFile2" 2>&1 | Out-Null
    
    if (Test-Path $tmpFile2) {
        try {
            $jsonContent = Get-Content $tmpFile2 -Raw | ConvertFrom-Json
            Write-Host "  [PASS] Snapshot JSON to file" -ForegroundColor Green
            $script:PassCount++
        } catch {
            Write-Host "  [FAIL] Snapshot JSON to file (invalid JSON)" -ForegroundColor Red
            $script:FailCount++
        }
        Remove-Item $tmpFile2 -ErrorAction SilentlyContinue
    }
}

# ============================================================================
# SECTION 11: MONITOR OPERATIONS
# ============================================================================

if (-not $script:NoDevice) {
    Write-TestSection "Monitor Operations"
    
    # Device monitoring
    Test-Command "Monitor devices (1s)" "monitor 1" -SkipIfNoDevice $true
    
    # Property monitoring
    if ($script:DeviceCaps -and $script:DeviceCaps.VideoProps.Count -gt 0) {
        $prop = $script:DeviceCaps.VideoProps.Keys | Select-Object -First 1
        
        Write-Host "  [INFO] Testing property monitor on vid.$prop (2s)" -ForegroundColor Blue
        
        $job = Start-Job -ScriptBlock {
            param($exe, $p)
            & $exe "monitor" "0" "vid" "$p" "--interval=1" 2>&1 | Out-String
        } -ArgumentList $CLI, $prop
        
        Start-Sleep -Seconds 2
        Stop-Job $job -ErrorAction SilentlyContinue
        $output = Receive-Job $job
        Remove-Job $job -ErrorAction SilentlyContinue
        
        if ($output -match "Monitoring|$prop=") {
            Write-Host "  [PASS] Property monitor" -ForegroundColor Green
            $script:PassCount++
            $script:TestResults += [PSCustomObject]@{Test="Property monitor"; Status="PASS"}
        } else {
            Write-Host "  [FAIL] Property monitor" -ForegroundColor Red
            $script:FailCount++
            $script:TestResults += [PSCustomObject]@{Test="Property monitor"; Status="FAIL"}
        }
    }
}

# ============================================================================
# SECTION 12: VALIDATION & ERROR HANDLING
# ============================================================================

if (-not $script:NoDevice -and $script:DeviceCaps) {
    Write-TestSection "Property Validation"
    
    if ($script:DeviceCaps.VideoProps.Count -gt 0) {
        $prop = $script:DeviceCaps.VideoProps.Keys | Select-Object -First 1
        $info = $script:DeviceCaps.VideoProps[$prop]
        
        # Out of range
        $badVal = $info.Max + 9999
        Test-Command "Reject out of range" "set 0 vid $prop $badVal" -ShouldSucceed $false -SkipIfNoDevice $true
        
        # Step misalignment (if step > 1)
        if ($info.Step -gt 1) {
            $badStep = $info.Min + 1
            if (($badStep - $info.Min) % $info.Step -ne 0) {
                Test-Command "Reject step-misaligned" "set 0 vid $prop $badStep" -ShouldSucceed $false -SkipIfNoDevice $true
            }
        }
    }
}

Write-TestSection "Error Handling"

Test-Command "Invalid device index" "get 999 cam Pan" -ShouldSucceed $false
Test-Command "Invalid domain" "get 0 invaliddom Pan" -ShouldSucceed $false
Test-Command "Invalid property" "get 0 cam FakeProperty" -ShouldSucceed $false
Test-Command "Missing arguments" "get 0" -ShouldSucceed $false
Test-Command "Unknown command" "fakecommand" -ShouldSucceed $false
Test-Command "Invalid flag combo" "-z list" -ShouldSucceed $false

# ============================================================================
# SUMMARY
# ============================================================================

Write-TestHeader "Test Summary"

$total = $script:PassCount + $script:FailCount + $script:SkipCount

Write-Host ""
Write-Host "Total:   $total"
Write-Host "Passed:  $($script:PassCount)" -ForegroundColor Green
Write-Host "Failed:  $($script:FailCount)" -ForegroundColor Red
Write-Host "Skipped: $($script:SkipCount)" -ForegroundColor Yellow
Write-Host ""

$passRate = if($total -gt 0){[math]::Round(($script:PassCount / $total) * 100, 2)}else{0}
Write-Host "Pass Rate: $passRate%"

# Failed tests
if ($script:FailCount -gt 0) {
    Write-Host "`nFailed Tests:" -ForegroundColor Red
    $script:TestResults | Where-Object {$_.Status -eq "FAIL" -or $_.Status -eq "ERROR"} | ForEach-Object {
        Write-Host "  - $($_.Test)" -ForegroundColor Red
        if ($_.Command) {
            Write-Host "    $($_.Command)" -ForegroundColor DarkGray
        }
    }
}

# Save results
$resultFile = "duvc-test-results.json"
$summary = @{
    Timestamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    CLI = $CLI
    DevicePresent = $hasDevice
    NoDeviceMode = $script:NoDevice
    Total = $total
    Passed = $script:PassCount
    Failed = $script:FailCount
    Skipped = $script:SkipCount
    PassRate = $passRate
    Tests = $script:TestResults
    DeviceCapabilities = if($script:DeviceCaps){@{
        CameraCount = $script:DeviceCaps.CameraProps.Count
        VideoCount = $script:DeviceCaps.VideoProps.Count
        CameraProperties = @($script:DeviceCaps.CameraProps.Keys)
        VideoProperties = @($script:DeviceCaps.VideoProps.Keys)
    }}else{$null}
}

$summary | ConvertTo-Json -Depth 5 | Out-File $resultFile -Encoding UTF8
Write-Host "`nResults: $resultFile" -ForegroundColor Cyan

# Capability summary
if ($script:DeviceCaps) {
    Write-Host "`nDevice Capabilities:" -ForegroundColor Cyan
    Write-Host "  Camera: $($script:DeviceCaps.CameraProps.Count) ($($script:DeviceCaps.CameraProps.Keys -join ', '))"
    Write-Host "  Video:  $($script:DeviceCaps.VideoProps.Count) ($($script:DeviceCaps.VideoProps.Keys -join ', '))"
}

exit $(if($script:FailCount -gt 0){1}else{0})


# ============================================================================
# USAGE
# ============================================================================
# # With device connected
# .\test-duvc-cli.ps1

# # Verbose mode
# .\test-duvc-cli.ps1 -Verbose

# # No device mode (CI/CD)
# .\test-duvc-cli.ps1 -NoDevice

# # Custom CLI path
# .\test-duvc-cli.ps1 -CLI ".\build\Release\duvc-cli.exe"

# # Combined
# .\test-duvc-cli.ps1 -CLI ".\build\duvc-cli.exe" -NoDevice -Verbose
