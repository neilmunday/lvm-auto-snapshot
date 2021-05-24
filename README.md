# lvm-auto-snapshot

A script that can be used to automatically create LVM snapshots for back-up purposes.

## Usage

Example usage to keep back-up snapshots for 7 days where each snapshot is 10GB in size. Any snapshots that are older than `--days` will be deleted.

```
./lvm-auto-snapshot.py --days 7 --size 10 --vg storage --lv docs
```

If you run `lvs` you will see your snapshots, e.g.

```
# lvs storage
  LV                     VG      Attr       LSize   Pool Origin Data%  Meta%  Move Log Cpy%Sync Convert
  docs                   storage owi-aor--- 200.00g                                    100.00
  docs_backup_2021.05.24 storage sri-a-s---  10.00g      docs   0.01
```

The script can for example be used as a cron job to create daily back-ups:

```
0       15      *       *       *       root    /usr/local/sbin/lvm-auto-snapshot.py -d 7 -g storage -l docs  -s 10 -k 7 > /var/log/lv_snapshot_docs.log  2>&1
```

## Auto expansion of snapshots

LVM has the ability to automatically expand snapshot volumes when they are almost full. By default this is not enabled. If you want to enable this feature then you will need to edit `/etc/lvm/lvm.conf` and set the following parameters:

```
snapshot_autoextend_threshold = 90
snapshot_autoextend_percent = 20
```

Now restart `lvm2-monitor`:

```
systemctl restart lvm2-monitor
```

`snapshot_autoextend_threshold` must be less than 100 in order to enable auto expansion of snapshot volumes. In this example when a snapshot volume reaches 90% capacity, LVM will automatically expand the logical volume by 20%.
