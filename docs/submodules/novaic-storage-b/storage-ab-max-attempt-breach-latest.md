# Storage-A/B Max-Attempt Breach Injection Evidence

- command: `bash scripts/failure_injection_max_attempt_breach.sh`
- scenario: Storage-A permanently offline; Storage-B retry exhausts `STORAGE_B_RESOLVE_MAX_RETRIES=3`
- expected_marker: `RETRY_MAX_BREACH_RESOLVER_NULL=PASS`
- expected_marker: `RETRY_MAX_BREACH_ATTEMPTS_SEEN=3`
- expected_marker: `RETRY_MAX_BREACH_STOP=PASS`
- result_id: `trs_98dc9ac5`
- fake_file_url: `http://127.0.0.1:39895/api/files/fake/image.png`
- logs: `/var/folders/n3/_7qrtb716jg07p9d71216l3m0000gn/T//novaic-max-breach-45910/logs/storage-b.log`
