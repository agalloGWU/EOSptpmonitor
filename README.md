# EOSptpmonitor
Grab PTP monitor data from Arista EOS and store in SQLite3 database

## PTP monitor data
Arista EOS keeps track of the last 100 PTP records, which include:
 * `lastSyncSeqId` (Last sequenceId of sync / followUp PTP message processed.)
 * `realLastSyncTime` (Epoch timestamp (in ns) of when the PTP data has been detected.)
 * `meanPathDelay` (ns)
 * `Interface` (Slave interface on which the PTP data has been recorded.)
 * `offsetFromMaster` (ns)
 * `skew` (Ratio of master's second to local second.)

lastSyncSeqId is used the Primary Key in the database to ensure duplicate data is not inserted

Script should be run each minute via cron to ensure we get all the data

