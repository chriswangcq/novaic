# Desktop Round 012 Replay Bundle

## Clean-Clone Setup
```bash
git clone git@github.com:chriswangcq/novaic.git
cd novaic
pip install -r novaic-desktop/requirements.txt
```

## Success Path
```
DESKTOP_SPLIT_CONFIG_ABORT=PASS
DESKTOP_SPLIT_CONFIG_ABORT_EXIT_CODE=1
```

## Failure Path
```
FAIL_PATH_DESKTOP_SPLIT_CONFIG=PASS
```

## Marker Index
- DESKTOP_SPLIT_CONFIG_ABORT=PASS
- FAIL_PATH_DESKTOP_SPLIT_CONFIG=PASS
