import pyvisa
import csv
import time
from datetime import datetime

RAILS = {
    "3V6": {"nominal": 3.6, "max_i": 2.5},
    "1V8": {"nominal": 1.8, "max_i": 3.0},
    "3V3": {"nominal": 3.3, "max_i": 3.0},
    "2V5": {"nominal": 2.5, "max_i": 1.5},
}

volt_tolerance= 0.05
ripple_limit  = 50
undershoot_limit = 0.10
recovery_limit = 1.0

def connect_instruments():
    rm    = pyvisa.ResourceManager()
    psu   = rm.open_resource('GPIB0::5::INSTR')
    eload = rm.open_resource('GPIB0::6::INSTR')
    dmm   = rm.open_resource('GPIB0::7::INSTR')
    scope = rm.open_resource('GPIB0::8::INSTR')
    for inst in [psu, eload, dmm, oscilloscope]:
      inst.timeout = 5000
    return psu, eload, dmm, oscilloscope

def configure_psu(psu):
    psu.write('*RST')
    psu.write('INST:SEL CH1')
    psu.write('VOLT 5.0')
    psu.write('CURR 3.0')
    psu.write('OUTP ON')
    time.sleep(1)

def configure_oscilloscope(oscilloscope):
    oscilloscope.write('*RST')
    oscilloscope.write('CHAN1:DISP ON')
    oscilloscope.write('CHAN1:SCAL 0.1')
    oscilloscope.write('TIM:SCAL 0.001')
    osciloscope.write('BAND1 20E6')
    oscilloscope.write('CHAN1:COUP AC')

def run_transient_test(eload, osciloscope, dmm, rail_name, rail_cfg):
    results  = []
    nominal  = rail_cfg["nominal"]
    imax     = rail_cfg["max_i"]
    light    = imax * 0.1 #it is the load when it is 10% of the load

    for capture in range(10):
        eload.write(f'CURR {light:.3f}')
        time.sleep(0.05)
        eload.write(f'CURR {imax:.3f}')
        time.sleep(0.002)

        vdc  = float(dmm.query('MEAS:VOLT:DC?'))
        vmax = float(scope.query('MEAS:VMAX? CHAN1'))
        vmin = float(scope.query('MEAS:VMIN? CHAN1'))

        ripple_mv     = (vmax - vmin) * 1000
        undershoot_mv = (nominal - vmin) * 1000
        recovery_ms   = float(
            scope.query('MEAS:TINT? CHAN1')
        ) * 1000
        #here we need to test all tests that okay or not
        volt_ok   = abs(vdc - nominal) <= nominal * volt_tolerance
        ripple_ok = ripple_mv <= ripple_limit
        undershoot_ok = undershoot_mv <= nominal * undershoot_limit * 1000
        recovery_ok = recovery_ms <= recovery_limit

        status = "PASS" 
        if 
        all([volt_ok, ripple_ok, undershoot_ok, recovery_ok])
        else 
        "FAIL"

        results.append({
            "timestamp": datetime.now().isoformat(),
            "rail": rail_name,
            "capture": capture + 1,#THIS is capturing
            "vdc_v": round(vdc, 4), #dc power
            "ripple_mv" : round(ripple_mv, 2),
            "undershoot_mv": round(undershoot_mv, 2),
            "recovery_ms"  : round(recovery_ms, 3),
            "v_pass": "PASS" 
            if volt_ok   
            else "FAIL",
            "rip_pass": "PASS"
            if ripple_ok 
            else "FAIL",
            "und_pass": "PASS" 
            if undershoot_ok 
            else "FAIL",
            "rec_pass": "PASS"
            if recovery_ok 
            else "FAIL",
            "status": status
        })

        print(f"  Capture {capture+1}/10: {status}")
        eload.write(f'CURR {light:.3f}')
        time.sleep(0.1)

    return results
#now after test all the if all passes need to save the results
def save_results(all_results):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename  = f'PDN_Test_{timestamp}.csv'
    with open(filename, 'w', newline='') as f:
    writer = csv.DictWriter(
        f, fieldnames=all_results[0].keys()
      )
        writer.writeheader()
        writer.writerows(all_results)
print(f'Results saved: {filename}')
    return filename
#need to generate the report also,
def generate_report(all_results):
    print("\n" + "="*40)
    print("load_transient_test_report")
    print("="*40)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("-"*40)

    overall = "PASS"

    for rail in RAILS:
        r       = [x for x in all_results if x['rail'] == rail]
        passes  = sum(1 for x in r if x['status'] == 'PASS')
        avg_ripple = sum(x['ripple_mv'] for x in r) / len(r)
        max_undershoot = max(x['undershoot_mv'] for x in r)
        max_recovery = max(x['recovery_ms'] for x in r)
        rail_status = "PASS" if passes == 10 else "FAIL"

        if rail_status == "FAIL":
            overall = "FAIL"

        print(f"\nRail: {rail}")
        print(f"  Pass Rate : {passes}/10")
        print(f"  Avg Ripple : {avg_ripple:.1f}mV")
        print(f"  Max Undershoot: {max_undershoot:.1f}mV")
        print(f"  Max Recovery: {max_recovery:.2f}ms")
        print(f"  Result : {rail_status}")

    print("\n" + "="*40)
    print(f"  OVERALL RESULT: {overall}")
    print("="*40 + "\n")

def main():
    print("Load Transient Testing")
    print("="*40)

    psu, eload, dmm, oscilloscope = connect_instruments()
    configure_psu(psu)
    configure_oscilloscope(osilloscope)

    all_results = []

    for rail_name, rail_cfg in RAILS.items():
        print(f"\nTesting {rail_name}...")
        results = run_transient_test(
            eload, oscilloscope, dmm, rail_name, rail_cfg
        )
        all_results.extend(results)

    csv_file = save_results(all_results)
    generate_report(all_results)

    psu.write('OUTP OFF')
    eload.write('OUTP OFF')
    print("Instruments OFF")
    print(f"Complete! Results: {csv_file}")

if __name__ == '__main__':
    main()
