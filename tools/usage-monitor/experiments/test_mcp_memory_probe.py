import unittest
from mcp_memory_probe import tool_result


class McpContentContracts(unittest.TestCase):
    def test_notice_does_not_corrupt_json_payload(self):
        result={'content':[{'type':'text','text':'{"entities": []}'},{'type':'text','text':'Existing entities were skipped; use add_observations.'}]}
        self.assertEqual(tool_result(result),{'entities':[]})
        self.assertEqual(len(result['content']),2)

    def test_explicit_structured_content_and_errors(self):
        self.assertEqual(tool_result({'structuredContent':{'entities':[]},'content':[]}),{'entities':[]})
        with self.assertRaises(RuntimeError):tool_result({'isError':True})
        with self.assertRaises(ValueError):tool_result({'content':[{'type':'text','text':'[]'},{'type':'text','text':'{}'}]})


if __name__=='__main__':unittest.main()
