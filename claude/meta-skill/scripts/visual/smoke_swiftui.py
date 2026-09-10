"""Build and capture bundled SwiftUI fixture on a new disposable simulator.

This checks capture plumbing, not user-approved design or independent review.
Usage: python3 smoke_swiftui.py OUTPUT_DIR
"""
import json
import plistlib
import subprocess
import sys
import tempfile
import time
from pathlib import Path


def run(*args, **kwargs):
    return subprocess.check_output(args, text=True, timeout=180, **kwargs).strip()


def _ver(text):
    return tuple(int(x) for x in str(text).split('.') if x.isdigit())


def pick_pair(runtimes, devicetypes):
    """Newest available iOS runtime paired with the newest iPhone that supports it; never an incompatible pair."""
    ios = sorted((r for r in runtimes if r.get('isAvailable') and r.get('name', '').startswith('iOS')),
                 key=lambda r: _ver(r.get('version')), reverse=True)
    phones = sorted((d for d in devicetypes if d.get('productFamily') == 'iPhone' or d.get('name', '').startswith('iPhone')),
                    key=lambda d: _ver(d.get('minRuntimeVersionString') or 0), reverse=True)
    if not ios:
        raise SystemExit('no available iOS simulator runtime; install one in Xcode > Settings > Components')
    for r in ios:
        v = _ver(r.get('version'))
        for d in phones:
            lo = _ver(d.get('minRuntimeVersionString') or '0')
            hi = _ver(d.get('maxRuntimeVersionString') or '999')
            if lo <= v <= hi:
                return r['identifier'], d['identifier'], str(r.get('version'))
    raise SystemExit('no iPhone device type is compatible with any installed iOS runtime')


def main(output):
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    runtime, device, version = pick_pair(
        json.loads(run('xcrun','simctl','list','runtimes','-j'))['runtimes'],
        json.loads(run('xcrun','simctl','list','devicetypes','-j'))['devicetypes'])
    major = version.split('.')[0] + '.0'
    udid = None
    try:
        with tempfile.TemporaryDirectory(prefix='visual-fixture-') as temp:
            app = Path(temp) / 'VisualFixture.app'
            app.mkdir()
            sdk = run('xcrun','--sdk','iphonesimulator','--show-sdk-path')
            source = Path(__file__).parent / 'fixtures/VisualFixture.swift'
            run('xcrun','swiftc','-parse-as-library','-sdk',sdk,'-target',f'arm64-apple-ios{major}-simulator',
                str(source),'-o',str(app / 'VisualFixture'))
            with (app / 'Info.plist').open('wb') as handle:
                plistlib.dump({'CFBundleIdentifier':'local.cross-exam.visual-fixture',
                    'CFBundleExecutable':'VisualFixture','CFBundleName':'VisualFixture',
                    'CFBundlePackageType':'APPL','CFBundleVersion':'1','CFBundleShortVersionString':'1.0',
                    'MinimumOSVersion':major,'LSRequiresIPhoneOS':True,'UILaunchScreen':{},
                    'UIDeviceFamily':[1,2]},handle)
            run('codesign','--force','--sign','-',str(app))
            udid = run('xcrun','simctl','create','CrossExam-Disposable',device,runtime)
            run('xcrun','simctl','boot',udid)
            subprocess.check_output(['xcrun','simctl','bootstatus',udid,'-b'], text=True, timeout=600)
            run('xcrun','simctl','install',udid,str(app))
            import os
            for appearance in ('light','dark'):
                run('xcrun','simctl','ui',udid,'appearance',appearance)
                for state in ('normal','loading','empty','error'):
                    subprocess.run(['xcrun','simctl','terminate',udid,'local.cross-exam.visual-fixture'],
                                   capture_output=True, timeout=30)
                    run('xcrun','simctl','launch',udid,'local.cross-exam.visual-fixture',
                        env={**os.environ,'SIMCTL_CHILD_FIXTURE_STATE':state})
                    time.sleep(2)
                    run('xcrun','simctl','io',udid,'screenshot',str(output / f'{state}-{appearance}.png'))
            (output / 'capture-context.json').write_text(json.dumps({'runtime':runtime,'device':device,'os':version,
                'udid':udid,'scope':'8 captures; plumbing smoke only, not visual acceptance'},indent=2))
    finally:
        if udid:
            subprocess.run(['xcrun','simctl','shutdown',udid],capture_output=True,timeout=60)
            subprocess.run(['xcrun','simctl','delete',udid],capture_output=True,timeout=60)


if __name__ == '__main__':
    main(sys.argv[1])
