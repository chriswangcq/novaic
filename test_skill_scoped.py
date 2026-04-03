import sys, time
sys.path.insert(0, 'novaic-compact-engine')
from compact_engine import *
from compact_engine.skill_scoped import SkillScopedCompactor, SkillCheckpoint, SkillPhase

print('=== Validating Skill-Scoped Compaction ===')

class MockSummarizer:
    def summarize(self, messages, max_tokens=2000, instructions=''):
        return 'Summarized LLM response: Skill successfully executed and updated 3 files.'

print('\\n[Test 1] With Summarizer')
compactor = SkillScopedCompactor(summarizer=MockSummarizer(), min_delta_messages=2, min_delta_tokens=10)

msgs = [
    Message(role=MessageRole.USER, content='Deploy the app'),
    Message(role=MessageRole.ASSISTANT, content='I will use the deploy skill'),
]

cp = compactor.checkpoint(msgs, skill_id='s1', skill_name='DeploySkill')
print(f'Checkpoint phase: {compactor.tracker.phase.value}, start_idx: {cp.start_index}')

msgs.append(Message(role=MessageRole.ASSISTANT, content='Running bash to deploy'))
msgs.append(Message(role=MessageRole.TOOL_RESULT, tool_name='bash', content='Success: /app/index.js modified'))
msgs.append(Message(role=MessageRole.ASSISTANT, content='Deploy finished.'))

result = compactor.compact(msgs)
assert result is not None, 'Compaction should trigger'
assert len(result.messages) == 3, f'Expected 3 messages, got {len(result.messages)}'
assert result.messages[2].role == MessageRole.ASSISTANT
assert 'Summarized LLM response' in result.messages[2].content
print(f'✅ Summarized correctly. Saved {result.tokens_saved} tokens.')
print(f'Final message content:\\n{result.messages[-1].content}')

print('\\n[Test 2] Rule-based Fallback')
compactor_fb = SkillScopedCompactor(min_delta_messages=2, min_delta_tokens=10)

msgs2 = [
    Message(role=MessageRole.SYSTEM, content='System prompt'),
]

compactor_fb.checkpoint(msgs2, skill_id='s2', skill_name='RefactorSkill')
msgs2.append(Message(role=MessageRole.ASSISTANT, content='Refactoring...'))
msgs2.append(Message(role=MessageRole.TOOL_RESULT, tool_name='file_edit', content='Modified /src/main.py'))
msgs2.append(Message(role=MessageRole.TOOL_RESULT, tool_name='bash', content='Error: lint failed on /src/main.py'))
msgs2.append(Message(role=MessageRole.ASSISTANT, content='Refactoring is done but there is a lint error.'))

result_fb = compactor_fb.compact(msgs2)
assert result_fb is not None
print(f'✅ Fallback extraction successfully triggered.')
print(f'Final fallback message:\\n{result_fb.messages[-1].content}')

print('\\n[Test 3] Skip when delta is too small')
compactor_skip = SkillScopedCompactor(min_delta_messages=5, min_delta_tokens=100)
msgs3 = [Message(role=MessageRole.USER, content='Hi')]
compactor_skip.checkpoint(msgs3, skill_id='s3', skill_name='TestSkip')
msgs3.append(Message(role=MessageRole.ASSISTANT, content='Short reply'))
result_skip = compactor_skip.compact(msgs3)
assert result_skip is None
print(f'✅ Correctly skipped small delta.')

print('\\n🎉 Skill-Scoped Compaction fully verified!')
