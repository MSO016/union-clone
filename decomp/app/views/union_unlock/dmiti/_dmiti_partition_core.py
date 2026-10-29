CHUNK_READ_BYTES = 512
CHUNK_WRITE_BYTES = 256
MAX_RETRIES = 3
PARTITION_BLACKLIST = ('preloader', 'sml', 'sml_a', 'sml_b', 'trustos', 'teecfg', 'uboot', 'uboot_a', 'uboot_b', 'splloader', 'splloader_a', 'splloader_b', 'efuse', 'seccfg', 'dpm')
PARTITION_WARN = ('boot', 'boot_a', 'boot_b', 'recovery', 'super', 'system', 'vendor', 'dtbo', 'vbmeta', 'vbmeta_a', 'vbmeta_b', 'l_modem', 'pm_sys', 'wcnmodem')
PARTITION_NOTES = {'persist': ('FRP', True), 'miscdata': ('PYJ/SEC', True), 'productinfo': ('IMEI', True), 'prodnv': ('CAL', True), 'wcnmodem': ('MODEM', True), 'l_modem': ('MODEM', True), 'userdata': ('DADOS', False), 'boot': ('BOOT', True), 'boot_a': ('BOOT', True), 'boot_b': ('BOOT', True), 'recovery': ('BOOT', True), 'super': ('SYSTEM', True), 'system': ('SYSTEM', True), 'preloader': ('PERIGO', True), 'splloader': ('PERIGO', True), 'sml': ('PERIGO', True), 'trustos': ('PERIGO', True), 'efuse': ('PERIGO', True)}
def format_size(size_mb):
    if size_mb >= 1024.0:
        return '%.1f GB' % (size_mb / 1024.0)
    if size_mb >= 1.0:
        return '%.1f MB' % size_mb
    return '%d KB' % int(size_mb * 1024)
def is_blacklisted(name):
    return name.lower().strip() in PARTITION_BLACKLIST
def is_warned(name):
    return name.lower().strip() in PARTITION_WARN
def get_note(name):
    nl = name.lower().strip()
    if nl in PARTITION_NOTES:
        return PARTITION_NOTES[nl]
    for key in PARTITION_NOTES:
        if key in nl:
            return PARTITION_NOTES[key]
    return ('', False)
