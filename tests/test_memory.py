from app.memory.conversation import ConversationMemory


async def test_conversation_memory_trims_old_messages():
    memory = ConversationMemory(max_messages=2)

    await memory.append_user("s1", "first")
    await memory.append_ai("s1", "second")
    await memory.append_user("s1", "third")

    messages = await memory.load("s1")
    assert len(messages) == 2
    assert messages[0].content == "second"
    assert messages[1].content == "third"
