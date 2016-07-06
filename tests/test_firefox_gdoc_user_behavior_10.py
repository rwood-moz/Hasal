from lib.perfBaseTest import PerfBaseTest


class TestSikuli(PerfBaseTest):

    def setUp(self):
        self.set_variable(test_target=self.env.TEST_TARGET_ID_BLANK_PAGE)
        super(TestSikuli, self).setUp()

    def test_firefox_gdoc_user_behavior_10(self):
        self.sikuli_status = self.sikuli.run_test( self.env.test_method_name,
                        self.env.test_method_name + "_" + self.env.time_stamp, test_url=self.test_url)
