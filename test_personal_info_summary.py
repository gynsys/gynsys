import asyncio
from types import SimpleNamespace

class DummyBot:
    async def edit_message_text(self, chat_id, message_id, text, reply_markup=None, parse_mode=None):
        print(f"EDIT [{chat_id}/{message_id}]:\n{text}\n")

class DummyUpdate:
    def __init__(self):
        self.effective_chat = SimpleNamespace(id=12345)
        self.callback_query = None

class DummyContext:
    def __init__(self, user_data):
        self.user_data = user_data
        self.bot = DummyBot()

async def test_show_personal_info_summary():
    from features.preconsulta.patient_flow.personal_info_handlers import show_personal_info_summary
    # Simula datos de usuario con HTML y otras patologías
    user_data = {
        'anchor_message_id': 1,
        'current_node_id': 'SHOW_SUMMARY',
        'full_name': 'Ana <b>García</b>',
        'age': '30',
        'ci': '12345678',
        'phone': '555-1234',
        'address': 'Calle <i>Falsa</i> 123',
        'occupation': 'Ingeniera',
        'family_history_mother': '<b>Diabetes</b>',
        'family_history_mother_other': '<i>Hipertensión</i>',
        'family_history_father': 'Ninguna',
        'family_history_father_other': '',
        'personal_history': '<b>Asma</b>',
        'personal_history_other': '<i>Alergia a penicilina</i>',
    }
    update = DummyUpdate()
    context = DummyContext(user_data)
    node = {}
    await show_personal_info_summary(update, context, node)

if __name__ == "__main__":
    asyncio.run(test_show_personal_info_summary())
