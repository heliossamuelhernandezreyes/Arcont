import copy
import json
from pathlib import Path
import unittest
from tools.production_finish import review

ROOT=Path(__file__).resolve().parents[1]

class FinishTests(unittest.TestCase):
    def setUp(self):
        self.profile=json.loads((ROOT/'templates/production/tps-mobile-finish.profile.json').read_text())
        self.record={"version":1,"scope":"godot-native-controlled-motion","engine":{"hash":"pinned-engine"},
            "source_hashes":{"motion.res":"a"*64},"cadence":[],"contacts":[],
            "grips":[{"hand":"L","error_m":0.001},{"hand":"R","error_m":0.001}],
            "visual_review":{"reviewer":"test fixture","notes":"synthetic fixture only"}}
        for case in self.profile['required_motion_cases']:
            self.record['cadence'].append({'case':case,'body_velocity_xz':[2,0],'foot_displacement_xz':[-1,0],'sample_seconds':0.5,'time_scale':1})
            for i in range(20):self.record['contacts'].append({'case':case,'foot':'L' if i%2 else 'R','position':[0,0,0],'anchor':[0,0,0],'time_s':i/60})

    def test_valid_technical_scope_is_not_art_or_device_approval(self):
        result=review(self.profile,self.record)
        self.assertTrue(result['technical_passed'])
        self.assertIn('not AAA',result['limits'][0])

    def test_old_cover_cadence_rejected(self):
        self.record['cadence'][2]['time_scale']=1.82/3.2
        result=review(self.profile,self.record)
        self.assertFalse(result['technical_passed'])

    def test_reversed_motion_rejected_even_when_speed_magnitude_matches(self):
        self.record['cadence'][3]['foot_displacement_xz']=[1,0]
        self.assertFalse(review(self.profile,self.record)['technical_passed'])

    def test_sliding_foot_rejected(self):
        self.record['contacts'][10]['position']=[0.12,0,0]
        self.assertFalse(review(self.profile,self.record)['technical_passed'])

    def test_invalid_and_missing_measurements(self):
        for change in ('nan','scope','missing_foot','missing_case','missing_review','zero_time'):
            with self.subTest(change=change):
                value=copy.deepcopy(self.record)
                if change=='nan':value['contacts'][0]['position'][0]=float('nan')
                if change=='scope':value['scope']='android-device'
                if change=='missing_foot':value['contacts']=[x for x in value['contacts'] if x['foot']=='L']
                if change=='missing_case':value['cadence'].pop()
                if change=='missing_review':value['visual_review']={}
                if change=='zero_time':value['cadence'][0]['sample_seconds']=0
                with self.assertRaises(ValueError):review(self.profile,value)

if __name__=='__main__':unittest.main()
