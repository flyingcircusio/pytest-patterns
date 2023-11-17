import pytest

GENERIC_HEADER = [
    "String did not meet the expectations.",
    "",
    "🟢=EXPECTED | ⚪️=OPTIONAL | 🟡=UNEXPECTED | 🔴=REFUSED/UNMATCHED",
    "",
    "Here is the string that was tested: ",
    "",
]


def test_patternslib_multiple_accesses(patterns):
    assert patterns.foo is patterns.foo


def test_empty_pattern_empty_string_is_ok(patterns):
    # This is fine IMHO. The whole general assumption is that we only reject
    # unexpected content and fail if required content is missing. If there is
    # no content, then there is no unexpected content and if you didn't expect
    # any content then there is none missing, so we fall through.
    audit = patterns.nothing._audit("")
    assert list(audit.report()) == GENERIC_HEADER
    assert audit.is_ok()


def test_unexpected_lines_fail(patterns):
    audit = patterns.nothing._audit("This is an unexpected line")
    assert list(audit.report()) == [
        *GENERIC_HEADER,
        "🟡                 | This is an unexpected line",
    ]
    assert not audit.is_ok()


def test_empty_lines_do_not_match(patterns):
    patterns.nothing.optional("")
    audit = patterns.nothing._audit(
        """
"""
    )
    assert list(audit.report()) == [
        *GENERIC_HEADER,
        "🟡                 | ",
    ]
    assert not audit.is_ok()


def test_empty_lines_match_special_marker(patterns):
    patterns.empty.optional("<empty-line>")
    audit = patterns.empty._audit(
        """

<empty-line>
"""
    )
    assert list(audit.report()) == [
        *GENERIC_HEADER,
        "⚪️ empty           | ",
        "⚪️ empty           | ",
        "⚪️ empty           | <empty-line>",
    ]
    assert audit.is_ok()


def test_comprehensive(patterns):
    sample = patterns.sample

    sample.in_order(
        """
This comes early on
This comes later

This comes even later
"""
    )
    sample.optional(
        """
This is a heartbeat that can appear almost anywhere...
"""
    )
    sample.continuous(
        """
This comes first (...)
This comes second (...)
This comes third (...)
"""
    )
    sample.refused(
        """
...error...
"""
    )
    assert (
        sample
        == """\
This comes early on
This is a heartbeat that can appear almost anywhere
This comes first (with variability)
This comes second (also with variability)
This comes third (more variability!)
This is a heartbeat that can appear almost anywhere (outside focus ranges)
This comes later
This comes even later
"""
    )


def test_in_order_lines_clear_with_intermittent_input(patterns):
    pattern = patterns.in_order
    pattern.in_order(
        """
This is a first expected line
This is a second expected line"""
    )
    pattern.optional("This is from another match")

    audit = pattern._audit(
        """\
This is a first expected line
This is from another match
This is a second expected line"""
    )

    assert list(audit.report()) == [
        *GENERIC_HEADER,
        "🟢 in_order        | This is a first expected line",
        "⚪️ in_order        | This is from another match",
        "🟢 in_order        | This is a second expected line",
    ]
    assert audit.is_ok()


def test_missing_ordered_lines_fail(patterns):
    pattern = patterns.in_order
    pattern.in_order(
        """
This is an expected line
This is also an expected line
"""
    )

    audit = pattern._audit(
        """\
This is an expected line
"""
    )
    assert list(audit.report()) == [
        *GENERIC_HEADER,
        "🟢 in_order        | This is an expected line",
        "",
        "These are the unmatched expected lines: ",
        "",
        "🔴 in_order        | This is also an expected line",
    ]
    assert not audit.is_ok()


def test_refused_lines_fail(patterns):
    pattern = patterns.refused
    pattern.refused("This is a refused line")

    audit = pattern._audit("This is a refused line")
    assert list(audit.report()) == [
        *GENERIC_HEADER,
        "🔴 refused         | This is a refused line",
        "",
        "These are the matched refused lines: ",
        "",
        "🔴 refused         | This is a refused line",
    ]
    assert not audit.is_ok()


def test_continuous_lines_only_clear_if_not_interrupted(patterns):
    pattern = patterns.focus
    pattern.optional("asdf")
    pattern.continuous(
        """
These lines
need to match
without being
interrupted
"""
    )

    audit = pattern._audit(
        """\
asdf
These lines
need to match
without being
interrupted
asdf
"""
    )
    assert list(audit.report()) == [
        *GENERIC_HEADER,
        "⚪️ focus           | asdf",
        "🟢 focus           | These lines",
        "🟢 focus           | need to match",
        "🟢 focus           | without being",
        "🟢 focus           | interrupted",
        "⚪️ focus           | asdf",
    ]
    assert audit.is_ok()

    audit = pattern._audit(
        """\
asdf
These lines
are broken
need to match
asdf
without being
because there is stuff in between
interrupted
asdf
"""
    )
    assert list(audit.report()) == [
        *GENERIC_HEADER,
        "⚪️ focus           | asdf",
        "🟢 focus           | These lines",
        "🔴 focus           | are broken",
        "🟡                 | need to match",
        "⚪️ focus           | asdf",
        "🟡                 | without being",
        "🟡                 | because there is stuff in between",
        "🟡                 | interrupted",
        "⚪️ focus           | asdf",
        "",
        "These are the unmatched expected lines: ",
        "",
        "🔴 focus           | need to match",
        "🔴 focus           | without being",
        "🔴 focus           | interrupted",
    ]
    assert not audit.is_ok()


def test_continuous_lines_fail_and_report_if_first_line_isnt_matching(patterns):
    pattern = patterns.focus
    pattern.continuous(
        """
First line
Second line
"""
    )

    audit = pattern._audit(
        """\
Not the first line
There is no first line
"""
    )
    assert list(audit.report()) == [
        *GENERIC_HEADER,
        "🟡                 | Not the first line",
        "🟡                 | There is no first line",
        "",
        "These are the unmatched expected lines: ",
        "",
        "🔴 focus           | First line",
        "🔴 focus           | Second line",
    ]
    assert not audit.is_ok()


def test_optional(patterns):
    pattern = patterns.optional
    pattern.optional("pong")
    pattern.optional("ping")

    audit = pattern._audit(
        """\
ping
"""
    )
    assert list(audit.report()) == [
        *GENERIC_HEADER,
        "⚪️ optional        | ping",
    ]
    assert audit.is_ok()


@pytest.fixture()
def fcqemu_patterns(patterns):
    patterns.debug.optional("simplevm> ...")

    # This part of the heartbeats must show up
    patterns.heartbeat.in_order(
        """
simplevm             heartbeat-initialized
simplevm             started-heartbeat-ping
simplevm             heartbeat-ping
"""
    )
    # The pings may happen more times and sometimes the stopping part
    # isn't visible because we terminate too fast.
    patterns.heartbeat.optional(
        """
simplevm             heartbeat-ping
simplevm             stopped-heartbeat-ping
"""
    )

    patterns.failure.refused("...fail...")


def test_complex_example(patterns, fcqemu_patterns):
    outmigration = patterns.outmigration
    outmigration.merge("debug", "heartbeat", "failure")

    outmigration.in_order(
        """
/nix/store/.../bin/fc-qemu -v outmigrate simplevm
load-system-config
simplevm             connect-rados                  subsystem='ceph'
simplevm             acquire-lock                   target='/run/qemu.simplevm.lock'
simplevm             acquire-lock                   count=1 result='locked' target='/run/qemu.simplevm.lock'
simplevm             qmp_capabilities               arguments={} id=None subsystem='qemu/qmp'
simplevm             query-status                   arguments={} id=None subsystem='qemu/qmp'

simplevm             outmigrate
simplevm             consul-register
simplevm             locate-inmigration-service
simplevm             check-staging-config           result='none'
simplevm             located-inmigration-service    url='http://host2.mgm.test.gocept.net:...'

simplevm             acquire-migration-locks
simplevm             check-staging-config           result='none'
simplevm             acquire-migration-lock         result='success' subsystem='qemu'
simplevm             acquire-local-migration-lock   result='success'
simplevm             acquire-remote-migration-lock
simplevm             acquire-remote-migration-lock  result='success'

simplevm             unlock                         subsystem='ceph' volume='rbd.ssd/simplevm.root'
simplevm             unlock                         subsystem='ceph' volume='rbd.ssd/simplevm.swap'
simplevm             unlock                         subsystem='ceph' volume='rbd.ssd/simplevm.tmp'

simplevm             prepare-remote-environment
simplevm             start-migration                target='tcp:192.168.4.7:...'
simplevm             migrate                        subsystem='qemu'
simplevm             migrate-set-capabilities       arguments={'capabilities': [{'capability': 'xbzrle', 'state': False}, {'capability': 'auto-converge', 'state': True}]} id=None subsystem='qemu/qmp'
simplevm             migrate-set-parameters         arguments={'compress-level': 0, 'downtime-limit': 4000, 'max-bandwidth': 22500} id=None subsystem='qemu/qmp'
simplevm             migrate                        arguments={'uri': 'tcp:192.168.4.7:...'} id=None subsystem='qemu/qmp'

simplevm             query-migrate-parameters       arguments={} id=None subsystem='qemu/qmp'
simplevm             migrate-parameters             announce-initial=50 announce-max=550 announce-rounds=5 announce-step=100 block-incremental=False compress-level=0 compress-threads=8 compress-wait-thread=True cpu-throttle-increment=10 cpu-throttle-initial=20 cpu-throttle-tailslow=False decompress-threads=2 downtime-limit=4000 max-bandwidth=22500 max-cpu-throttle=99 max-postcopy-bandwidth=0 multifd-channels=2 multifd-compression='none' multifd-zlib-level=1 multifd-zstd-level=1 subsystem='qemu' throttle-trigger-threshold=50 tls-authz='' tls-creds='' tls-hostname='' x-checkpoint-delay=20000 xbzrle-cache-size=67108864

simplevm             query-migrate                  arguments={} id=None subsystem='qemu/qmp'
simplevm             migration-status               mbps='-' remaining='0' status='setup'

simplevm             query-migrate                  arguments={} id=None subsystem='qemu/qmp'
simplevm             migration-status               mbps=... remaining='...' status='active'

simplevm             migration-status               mbps=... remaining='...' status='completed'

simplevm             query-status                   arguments={} id=None subsystem='qemu/qmp'
simplevm             finish-migration

simplevm             vm-destroy-kill-supervisor     attempt=1 subsystem='qemu'
simplevm             vm-destroy-kill-supervisor     attempt=2 subsystem='qemu'
simplevm             vm-destroy-kill-vm             attempt=1 subsystem='qemu'
simplevm             vm-destroy-kill-vm             attempt=2 subsystem='qemu'
simplevm             clean-run-files                subsystem='qemu'
simplevm             finish-remote
simplevm             consul-deregister
simplevm             outmigrate-finished            exitcode=0
simplevm             release-lock                   count=0 target='/run/qemu.simplevm.lock'
simplevm             release-lock                   result='unlocked' target='/run/qemu.simplevm.lock'
"""
    )
    # The migration process may take a couple of rounds to complete,
    # so this might appear more often:
    outmigration.optional(
        """
simplevm             query-migrate                  arguments={} id=None subsystem='qemu/qmp'
simplevm             migration-status               mbps=... remaining='...' status='active'
"""
    )

    assert (
        outmigration
        == """\
/nix/store/99xm8d2fjwlj6fvglrwpi0pz5zz8jsl1-python3.8-fc.qemu-dev/bin/fc-qemu -v outmigrate simplevm
load-system-config
simplevm             connect-rados                  subsystem='ceph'
simplevm             acquire-lock                   target='/run/qemu.simplevm.lock'
simplevm             acquire-lock                   count=1 result='locked' target='/run/qemu.simplevm.lock'
simplevm             qmp_capabilities               arguments={} id=None subsystem='qemu/qmp'
simplevm             query-status                   arguments={} id=None subsystem='qemu/qmp'
simplevm             outmigrate
simplevm             consul-register
simplevm             heartbeat-initialized
simplevm             locate-inmigration-service
simplevm             check-staging-config           result='none'
simplevm             located-inmigration-service    url='http://host2.mgm.test.gocept.net:43303'
simplevm             started-heartbeat-ping
simplevm             acquire-migration-locks
simplevm             heartbeat-ping
simplevm             check-staging-config           result='none'
simplevm             acquire-migration-lock         result='success' subsystem='qemu'
simplevm             acquire-local-migration-lock   result='success'
simplevm             acquire-remote-migration-lock
simplevm             acquire-remote-migration-lock  result='success'
simplevm             unlock                         subsystem='ceph' volume='rbd.ssd/simplevm.root'
simplevm             unlock                         subsystem='ceph' volume='rbd.ssd/simplevm.swap'
simplevm             unlock                         subsystem='ceph' volume='rbd.ssd/simplevm.tmp'
simplevm             prepare-remote-environment
simplevm             start-migration                target='tcp:192.168.4.7:2345'
simplevm             migrate                        subsystem='qemu'
simplevm             migrate-set-capabilities       arguments={'capabilities': [{'capability': 'xbzrle', 'state': False}, {'capability': 'auto-converge', 'state': True}]} id=None subsystem='qemu/qmp'
simplevm             migrate-set-parameters         arguments={'compress-level': 0, 'downtime-limit': 4000, 'max-bandwidth': 22500} id=None subsystem='qemu/qmp'
simplevm             migrate                        arguments={'uri': 'tcp:192.168.4.7:2345'} id=None subsystem='qemu/qmp'
simplevm             query-migrate-parameters       arguments={} id=None subsystem='qemu/qmp'
simplevm             migrate-parameters             announce-initial=50 announce-max=550 announce-rounds=5 announce-step=100 block-incremental=False compress-level=0 compress-threads=8 compress-wait-thread=True cpu-throttle-increment=10 cpu-throttle-initial=20 cpu-throttle-tailslow=False decompress-threads=2 downtime-limit=4000 max-bandwidth=22500 max-cpu-throttle=99 max-postcopy-bandwidth=0 multifd-channels=2 multifd-compression='none' multifd-zlib-level=1 multifd-zstd-level=1 subsystem='qemu' throttle-trigger-threshold=50 tls-authz='' tls-creds='' tls-hostname='' x-checkpoint-delay=20000 xbzrle-cache-size=67108864
simplevm             query-migrate                  arguments={} id=None subsystem='qemu/qmp'
simplevm             migration-status               mbps='-' remaining='0' status='setup'
simplevm> {'blocked': False, 'status': 'setup'}
simplevm             query-migrate                  arguments={} id=None subsystem='qemu/qmp'
simplevm             migration-status               mbps=0.32976 remaining='285,528,064' status='active'
simplevm> {'blocked': False,
simplevm>  'expected-downtime': 4000,
simplevm>  'ram': {'dirty-pages-rate': 0,
simplevm>          'dirty-sync-count': 1,
simplevm>          'duplicate': 182,
simplevm>          'mbps': 0.32976,
simplevm>          'multifd-bytes': 0,
simplevm>          'normal': 15,
simplevm>          'normal-bytes': 61440,
simplevm>          'page-size': 4096,
simplevm>          'pages-per-second': 10,
simplevm>          'postcopy-requests': 0,
simplevm>          'remaining': 285528064,
simplevm>          'skipped': 0,
simplevm>          'total': 286334976,
simplevm>          'transferred': 63317},
simplevm>  'setup-time': 1,
simplevm>  'status': 'active',
simplevm>  'total-time': 1418}
simplevm             query-migrate                  arguments={} id=None subsystem='qemu/qmp'
simplevm             migration-status               mbps=0.32976 remaining='285,331,456' status='active'
simplevm> {'blocked': False,
simplevm>  'expected-downtime': 4000,
simplevm>  'ram': {'dirty-pages-rate': 0,
simplevm>          'dirty-sync-count': 1,
simplevm>          'duplicate': 210,
simplevm>          'mbps': 0.32976,
simplevm>          'multifd-bytes': 0,
simplevm>          'normal': 35,
simplevm>          'normal-bytes': 143360,
simplevm>          'page-size': 4096,
simplevm>          'pages-per-second': 10,
simplevm>          'postcopy-requests': 0,
simplevm>          'remaining': 285331456,
simplevm>          'skipped': 0,
simplevm>          'total': 286334976,
simplevm>          'transferred': 145809},
simplevm>  'setup-time': 1,
simplevm>  'status': 'active',
simplevm>  'total-time': 3421}
simplevm             query-migrate                  arguments={} id=None subsystem='qemu/qmp'
simplevm             migration-status               mbps=0.18144 remaining='267,878,400' status='active'
simplevm> {'blocked': False,
simplevm>  'expected-downtime': 4000,
simplevm>  'ram': {'dirty-pages-rate': 0,
simplevm>          'dirty-sync-count': 1,
simplevm>          'duplicate': 4460,
simplevm>          'mbps': 0.18144,
simplevm>          'multifd-bytes': 0,
simplevm>          'normal': 46,
simplevm>          'normal-bytes': 188416,
simplevm>          'page-size': 4096,
simplevm>          'pages-per-second': 2500,
simplevm>          'postcopy-requests': 0,
simplevm>          'remaining': 267878400,
simplevm>          'skipped': 0,
simplevm>          'total': 286334976,
simplevm>          'transferred': 229427},
simplevm>  'setup-time': 1,
simplevm>  'status': 'active',
simplevm>  'total-time': 6253}
simplevm             heartbeat-ping
simplevm             query-migrate                  arguments={} id=None subsystem='qemu/qmp'
simplevm             migration-status               mbps=0.18144 remaining='226,918,400' status='active'
simplevm> {'blocked': False,
simplevm>  'expected-downtime': 4000,
simplevm>  'ram': {'dirty-pages-rate': 0,
simplevm>          'dirty-sync-count': 1,
simplevm>          'duplicate': 14460,
simplevm>          'mbps': 0.18144,
simplevm>          'multifd-bytes': 0,
simplevm>          'normal': 46,
simplevm>          'normal-bytes': 188416,
simplevm>          'page-size': 4096,
simplevm>          'pages-per-second': 2500,
simplevm>          'postcopy-requests': 0,
simplevm>          'remaining': 226918400,
simplevm>          'skipped': 0,
simplevm>          'total': 286334976,
simplevm>          'transferred': 319747},
simplevm>  'setup-time': 1,
simplevm>  'status': 'active',
simplevm>  'total-time': 10258}
simplevm             query-migrate                  arguments={} id=None subsystem='qemu/qmp'
simplevm             migration-status               mbps=0.18144 remaining='169,574,400' status='active'
simplevm> {'blocked': False,
simplevm>  'expected-downtime': 4000,
simplevm>  'ram': {'dirty-pages-rate': 0,
simplevm>          'dirty-sync-count': 1,
simplevm>          'duplicate': 28460,
simplevm>          'mbps': 0.18144,
simplevm>          'multifd-bytes': 0,
simplevm>          'normal': 46,
simplevm>          'normal-bytes': 188416,
simplevm>          'page-size': 4096,
simplevm>          'pages-per-second': 2500,
simplevm>          'postcopy-requests': 0,
simplevm>          'remaining': 169574400,
simplevm>          'skipped': 0,
simplevm>          'total': 286334976,
simplevm>          'transferred': 446195},
simplevm>  'setup-time': 1,
simplevm>  'status': 'active',
simplevm>  'total-time': 15917}
simplevm             heartbeat-ping
simplevm             query-migrate                  arguments={} id=None subsystem='qemu/qmp'
simplevm             migration-status               mbps=0.18144 remaining='87,654,400' status='active'
simplevm> {'blocked': False,
simplevm>  'expected-downtime': 4000,
simplevm>  'ram': {'dirty-pages-rate': 0,
simplevm>          'dirty-sync-count': 1,
simplevm>          'duplicate': 48460,
simplevm>          'mbps': 0.18144,
simplevm>          'multifd-bytes': 0,
simplevm>          'normal': 46,
simplevm>          'normal-bytes': 188416,
simplevm>          'page-size': 4096,
simplevm>          'pages-per-second': 2500,
simplevm>          'postcopy-requests': 0,
simplevm>          'remaining': 87654400,
simplevm>          'skipped': 0,
simplevm>          'total': 286334976,
simplevm>          'transferred': 626835},
simplevm>  'setup-time': 1,
simplevm>  'status': 'active',
simplevm>  'total-time': 23926}
simplevm             heartbeat-ping
simplevm             query-migrate                  arguments={} id=None subsystem='qemu/qmp'
simplevm             migration-status               mbps=0.32976 remaining='18,821,120' status='active'
simplevm> {'blocked': False,
simplevm>  'expected-downtime': 4000,
simplevm>  'ram': {'dirty-pages-rate': 0,
simplevm>          'dirty-sync-count': 1,
simplevm>          'duplicate': 65218,
simplevm>          'mbps': 0.32976,
simplevm>          'multifd-bytes': 0,
simplevm>          'normal': 93,
simplevm>          'normal-bytes': 380928,
simplevm>          'page-size': 4096,
simplevm>          'pages-per-second': 10,
simplevm>          'postcopy-requests': 0,
simplevm>          'remaining': 18821120,
simplevm>          'skipped': 0,
simplevm>          'total': 286334976,
simplevm>          'transferred': 971457},
simplevm>  'setup-time': 1,
simplevm>  'status': 'active',
simplevm>  'total-time': 35251}
simplevm             heartbeat-ping
simplevm             query-migrate                  arguments={} id=None subsystem='qemu/qmp'
simplevm             migration-status               mbps=0.32976 remaining='827,392' status='active'
simplevm> {'blocked': False,
simplevm>  'expected-downtime': 4000,
simplevm>  'ram': {'dirty-pages-rate': 0,
simplevm>          'dirty-sync-count': 1,
simplevm>          'duplicate': 69514,
simplevm>          'mbps': 0.32976,
simplevm>          'multifd-bytes': 0,
simplevm>          'normal': 190,
simplevm>          'normal-bytes': 778240,
simplevm>          'page-size': 4096,
simplevm>          'pages-per-second': 10,
simplevm>          'postcopy-requests': 0,
simplevm>          'remaining': 827392,
simplevm>          'skipped': 0,
simplevm>          'total': 286334976,
simplevm>          'transferred': 1409164},
simplevm>  'setup-time': 1,
simplevm>  'status': 'active',
simplevm>  'total-time': 46571}
simplevm             heartbeat-ping
simplevm             heartbeat-ping
simplevm             query-migrate                  arguments={} id=None subsystem='qemu/qmp'
simplevm             migration-status               mbps=0.32976 remaining='1,175,552' status='active'
simplevm> {'blocked': False,
simplevm>  'expected-downtime': 4000,
simplevm>  'ram': {'dirty-pages-rate': 4,
simplevm>          'dirty-sync-count': 2,
simplevm>          'duplicate': 69594,
simplevm>          'mbps': 0.32976,
simplevm>          'multifd-bytes': 0,
simplevm>          'normal': 303,
simplevm>          'normal-bytes': 1241088,
simplevm>          'page-size': 4096,
simplevm>          'pages-per-second': 10,
simplevm>          'postcopy-requests': 0,
simplevm>          'remaining': 1175552,
simplevm>          'skipped': 0,
simplevm>          'total': 286334976,
simplevm>          'transferred': 1874632},
simplevm>  'setup-time': 1,
simplevm>  'status': 'active',
simplevm>  'total-time': 57893}
simplevm             heartbeat-ping
simplevm             query-migrate                  arguments={} id=None subsystem='qemu/qmp'
simplevm             migration-status               mbps=0.32976 remaining='172,032' status='active'
simplevm> {'blocked': False,
simplevm>  'expected-downtime': 4000,
simplevm>  'ram': {'dirty-pages-rate': 0,
simplevm>          'dirty-sync-count': 3,
simplevm>          'duplicate': 69730,
simplevm>          'mbps': 0.32976,
simplevm>          'multifd-bytes': 0,
simplevm>          'normal': 416,
simplevm>          'normal-bytes': 1703936,
simplevm>          'page-size': 4096,
simplevm>          'pages-per-second': 10,
simplevm>          'postcopy-requests': 0,
simplevm>          'remaining': 172032,
simplevm>          'skipped': 0,
simplevm>          'total': 286334976,
simplevm>          'transferred': 2340590},
simplevm>  'setup-time': 1,
simplevm>  'status': 'active',
simplevm>  'total-time': 69217}
simplevm             heartbeat-ping
simplevm             query-migrate                  arguments={} id=None subsystem='qemu/qmp'
simplevm             migration-status               mbps=0.34051462695157925 remaining='0' status='completed'
simplevm> {'blocked': False,
simplevm>  'downtime': 7,
simplevm>  'ram': {'dirty-pages-rate': 0,
simplevm>          'dirty-sync-count': 5,
simplevm>          'duplicate': 69730,
simplevm>          'mbps': 0.34051462695157925,
simplevm>          'multifd-bytes': 0,
simplevm>          'normal': 458,
simplevm>          'normal-bytes': 1875968,
simplevm>          'page-size': 4096,
simplevm>          'pages-per-second': 10,
simplevm>          'postcopy-requests': 0,
simplevm>          'remaining': 0,
simplevm>          'skipped': 0,
simplevm>          'total': 286334976,
simplevm>          'transferred': 2512989},
simplevm>  'setup-time': 1,
simplevm>  'status': 'completed',
simplevm>  'total-time': 69496}
simplevm             query-status                   arguments={} id=None subsystem='qemu/qmp'
simplevm             finish-migration
simplevm             vm-destroy-kill-supervisor     attempt=1 subsystem='qemu'
simplevm             vm-destroy-kill-supervisor     attempt=2 subsystem='qemu'
simplevm             vm-destroy-kill-vm             attempt=1 subsystem='qemu'
simplevm             vm-destroy-kill-vm             attempt=2 subsystem='qemu'
simplevm             clean-run-files                subsystem='qemu'
simplevm             finish-remote
simplevm             consul-deregister
simplevm             outmigrate-finished            exitcode=0
simplevm             release-lock                   count=0 target='/run/qemu.simplevm.lock'
simplevm             release-lock                   result='unlocked' target='/run/qemu.simplevm.lock'
"""
    )


def test_html(patterns):
    patterns.owrap.in_order(
        """
<!DOCTYPE html>
<html lang="en">
      <body>
      </body>
</html>
"""
    )
    patterns.owrap.optional("...")
    # patterns.owrap.normalize("html")

    invoice_list = patterns.invoice_list
    invoice_list.merge("owrap")
    invoice_list.continuous(
        """
      <tbody>
        <tr>
          <td>2023-10-01 &mdash; 2023-10-31</td>
          <td>
            <a href="https://localhost/customer/10466">
              10466</a>
            Theune, Christian
          </td>


            <td class="text-right numeric">
              0.00&nbsp;€
            </td>

          <td>pending</td>
          <td><a href="https://localhost/invoice/55006/view">View</a></td> </tr>
      </tbody>
"""
    )

    assert (
        invoice_list
        == """\
<!DOCTYPE html>
<html lang="en">
      <!-- This is a partial template for non-boosted HTMX requests where we only
      expect the body of the targetted template to be filled in. -->
      <body>


   <a
      href="https://localhost/invoice/generate"
      id="generateInvoices"
      class="list-group-item">
      <span class="glyphicon glyphicon-plus"></span> Generate
    </a>


            <div></div>
            <div class="well">
    <form
          class="form" role="form" id="filterForm"
          hx-get="https://localhost/invoice"
          hx-target="#invoiceTable"
          hx-trigger="change, submit, every 5s"
          hx-indicator="#invoiceTable"
          hx-push-url="true"
          hx-select="#invoiceTable"
          hx-select-oob="#invoiceStatus"
          >
      <div class="form-group">
        <input
               placeholder="Search ..."
               _="on load call me.focus()"
               class="form-control" name="search" value="Theun" />
      </div>

      <div class="form-group">
        <select class="form-control" name="timeframe">
          <option value="filter_this_month"> This month
          </option>
          <option value="filter_last_month" selected="True"> Last month
          </option>
          <option value="filter_this_year"> This year
          </option>
          <option value="filter_last_year"> Last year
          </option>
          <option value="filter_all"> All
          </option>
        </select>
      </div>

      <div class="form-group" id="invoiceStatus">
        <h4>Status</h4>

        <div class="checkbox">
          <label>
            <input type="checkbox" name="status" value="generating" checked="True" /> Generating (0)
          </label>
        </div>
        <div class="checkbox">
          <label>
            <input type="checkbox" name="status" value="pending" checked="True" /> Pending (72)
          </label>
        </div>
        <div class="checkbox">
          <label>
            <input type="checkbox" name="status" value="proforma" /> Proforma
          </label>
        </div>
        <div class="checkbox">
          <label>
            <input type="checkbox" name="status" value="review" checked="True" /> Review
          </label>
        </div>
        <div class="checkbox">
          <label>
            <input type="checkbox" name="status" value="error" checked="True" /> Error (0)
          </label>
        </div>
        <div class="checkbox">
          <label>
            <input type="checkbox" name="status" value="transmitted" checked="True" /> Transmitted
          </label>
        </div>

      </div>

      <div class="form-group">
        <h4>Options</h4>

        <div class="checkbox">
          <label>
            <input type="checkbox" name="compare" value="compare" /> Show trend
          </label>
        </div>

      </div>

    </form>
  </div>
            <div>
    <table class="table table-striped" id="invoiceTable">
      <thead>
        <tr>
          <th class="col-md-3">Consumption Period</th>
          <th class="col-md-3">Customer</th>

          <th class="col-md-1 text-right">Sum</th>
          <th class="col-md-1">Status</th>
          <th class="col-md-1">&nbsp;</th>
        </tr>
        <tr>
          <td>1 matching invoices.</td>
        </tr>
      </thead>

      <tbody>
        <tr>
          <td>2023-10-01 &mdash; 2023-10-31</td>
          <td>
            <a href="https://localhost/customer/10466">
              10466</a>
            Theune, Christian
          </td>


            <td class="text-right numeric">
              0.00&nbsp;€
            </td>

          <td>pending</td>
          <td><a href="https://localhost/invoice/55006/view">View</a></td> </tr>
      </tbody>
    </table>
  </div>
      </body>
</html>
"""
    )


# def test_ring0_json_api(patterns):
#     ring0 = patterns.ring0

#     ring0.normalize("json")
#     ring0.optional("...")
#     ring0.in_order(
#         """
# {
#         "directory_password": "gfhdjk",
# }
# """
#     )

#     ring0 == {
#         "aliases_fe": [],
#         "aliases_srv": [],
#         "directory_password": "gfhdjk",
#         "profile": "generic",
#         "creation_date": "2014-01-02T03:04:05+00:00",
#         "directory_ring": 0,
#         "environment": "testing",
#         "environment_class": "Puppet",
#         "environment_url": "",
#         "kvm_net_memory": 61440,
#         "machine": "physical",
#         "servicing": True,
#         "location": "ny",
#         "frontend_ips_v4": 1,
#         "frontend_ips_v6": 1,
#         "production": True,
#         "service_description": "backup server",
#         "secrets": {},
#         "secret_salt": "secret/salt",
#         "reverses": {"172.21.2.2": "test.gocept.net."},
#         "in_transit": False,
#         "interfaces": {
#             "fe": {
#                 "mac": "00:15:17:91:d2:f0",
#                 "bridged": False,
#                 "policy": "puppet",
#                 "gateways": {
#                     "172.21.2.0/24": "172.21.2.1",
#                     "2002:470:9aaf:42::/64": "2002:470:9aaf:42::1",
#                 },
#                 "networks": {
#                     "2002:470:9aaf:42::/64": ["2002:470:9aaf:42::2"],
#                     "172.21.2.0/24": ["172.21.2.2"],
#                 },
#             },
#             "ipmi": {
#                 "mac": "",
#                 "bridged": False,
#                 "policy": "puppet",
#                 "gateways": {"172.21.1.0/24": "172.21.1.1"},
#                 "networks": {"172.21.1.0/24": ["172.21.1.2"]},
#             },
#             "mgm": {
#                 "mac": "00:1e:c9:ad:4a:a6",
#                 "bridged": False,
#                 "policy": "puppet",
#                 "gateways": {
#                     "172.21.1.0/24": "172.21.1.1",
#                     "2002:470:9aaf:41::/64": "2002:470:9aaf:41::1",
#                 },
#                 "networks": {
#                     "2002:470:9aaf:41::/64": ["2002:470:9aaf:41::2"],
#                     "172.21.1.0/24": ["172.21.1.3"],
#                 },
#             },
#             "srv": {
#                 "mac": "00:1e:c9:ad:4a:a0",
#                 "bridged": False,
#                 "policy": "puppet",
#                 "gateways": {
#                     "172.21.3.0/24": "172.21.3.1",
#                     "2002:470:9aaf:43::/64": "2002:470:9aaf:43::1",
#                 },
#                 "networks": {
#                     "2002:470:9aaf:43::/64": ["2002:470:9aaf:43::2"],
#                     "172.21.3.0/24": ["172.21.3.2"],
#                 },
#             },
#             "sto": {
#                 "mac": "00:1e:c9:ad:4a:a2",
#                 "bridged": False,
#                 "policy": "puppet",
#                 "gateways": {
#                     "172.21.4.0/24": "172.21.4.1",
#                     "2002:470:9aaf:44::/64": "2002:470:9aaf:44::1",
#                 },
#                 "networks": {
#                     "2002:470:9aaf:44::/64": ["2002:470:9aaf:44::2"],
#                     "172.21.4.0/24": ["172.21.4.2"],
#                 },
#             },
#         },
#         "rack": "OB 4 DA",
#         "resource_group": "services",
#         "resource_group_parent": "",
#         "timezone": "UTC",
#         "id": 4100,
#         "nixos_configs": {},
#     }
