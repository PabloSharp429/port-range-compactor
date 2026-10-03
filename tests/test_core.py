import unittest

from port_range_compactor import compact_ports, compact_ports_from_list


class TestCompactPortsFromList(unittest.TestCase):

    def test_empty_input_returns_empty_string(self):
        self.assertEqual(compact_ports_from_list([]), "")

    def test_single_port(self):
        self.assertEqual(compact_ports_from_list([22]), "22")

    def test_consecutive_run_becomes_dash(self):
        self.assertEqual(compact_ports_from_list([80, 81, 82]), "80-82")

    def test_mixed_singles_and_runs(self):
        self.assertEqual(
            compact_ports_from_list([22, 80, 81, 82, 443]),
            "22,80-82,443",
        )

    def test_duplicates_removed(self):
        self.assertEqual(compact_ports_from_list([80, 81, 82, 80, 81]), "80-82")

    def test_unsorted_input_is_sorted(self):
        self.assertEqual(
            compact_ports_from_list([443, 82, 80, 22, 81]),
            "22,80-82,443",
        )

    def test_numeric_strings_accepted(self):
        self.assertEqual(compact_ports_from_list(["22", "80", "81"]), "22,80-81")

    def test_whitespace_around_string_tokens(self):
        self.assertEqual(compact_ports_from_list(["  22 ", " 80 "]), "22,80")

    def test_non_consecutive_ports_rendered_comma_separated(self):
        self.assertEqual(compact_ports_from_list([1, 3, 5]), "1,3,5")

    def test_two_consecutive_ports_use_dash(self):
        self.assertEqual(compact_ports_from_list([100, 101]), "100-101")

    def test_full_valid_range_is_accepted(self):
        self.assertEqual(compact_ports_from_list([0, 65535]), "0,65535")

    def test_out_of_range_high_raises(self):
        with self.assertRaises(ValueError):
            compact_ports_from_list([70000])

    def test_negative_port_raises(self):
        with self.assertRaises(ValueError):
            compact_ports_from_list([-1])

    def test_empty_string_token_in_list_raises(self):
        with self.assertRaises(ValueError):
            compact_ports_from_list([""])

    def test_non_numeric_string_raises(self):
        with self.assertRaises(ValueError):
            compact_ports_from_list(["abc"])

    def test_bool_rejected_explicitly(self):
        with self.assertRaises(TypeError):
            compact_ports_from_list([True])

    def test_none_rejected(self):
        with self.assertRaises(TypeError):
            compact_ports_from_list([None])

    def test_generator_input(self):
        gen = (i for i in [1, 2, 3])
        self.assertEqual(compact_ports_from_list(gen), "1-3")


class TestCompactPortsString(unittest.TestCase):

    def test_empty_string_returns_empty(self):
        self.assertEqual(compact_ports(""), "")

    def test_whitespace_only_returns_empty(self):
        self.assertEqual(compact_ports("   "), "")

    def test_already_compact_round_trips(self):
        self.assertEqual(compact_ports("22,80-82,443"), "22,80-82,443")

    def test_expands_and_recompacts(self):
        self.assertEqual(compact_ports("80,81,82"), "80-82")

    def test_dedup_in_string_form(self):
        self.assertEqual(compact_ports("80,81,82,80"), "80-82")

    def test_merges_overlapping_ranges(self):
        self.assertEqual(compact_ports("80-82,81-84"), "80-84")

    def test_unsorted_tokens_sorted(self):
        self.assertEqual(compact_ports("443,80,81"), "80-81,443")

    def test_malformed_range_start_missing_raises(self):
        with self.assertRaises(ValueError):
            compact_ports("-82")

    def test_malformed_range_end_missing_raises(self):
        with self.assertRaises(ValueError):
            compact_ports("80-")

    def test_range_backwards_raises(self):
        with self.assertRaises(ValueError):
            compact_ports("82-80")

    def test_out_of_range_in_string_raises(self):
        with self.assertRaises(ValueError):
            compact_ports("70000")

    def test_empty_token_between_commas_raises(self):
        with self.assertRaises(ValueError):
            compact_ports("80,,82")

    def test_non_string_input_raises(self):
        with self.assertRaises(TypeError):
            compact_ports([80, 81])

    def test_whitespace_around_tokens(self):
        self.assertEqual(compact_ports("  22 , 80 - 82 "), "22,80-82")


if __name__ == "__main__":
    unittest.main()
