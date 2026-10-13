import pytest
from test_provider import setup


@pytest.mark.parametrize('previous_query',['','Câu hỏi cũ'])
def test_prefetch_retrieves_current_question_without_matching_warm_cache(tmp_path,previous_query):
    runtime,config,memory=setup(tmp_path)
    memory.initialize('a',hermes_home=str(tmp_path))
    if previous_query:
        memory.queue_prefetch(previous_query,session_id='a')
    result=memory.prefetch('Câu hỏi mới về nghiệm thu?',session_id='a')
    assert 'bằng chứng gốc' in result
