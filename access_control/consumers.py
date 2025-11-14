import json
from channels.generic.websocket import AsyncWebsocketConsumer

class StudentAccessConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # WebSocket bog'langanda
        self.turnstile_id = None  # Hozircha turniket tanlanmagan
        self.room_group_name = None

        await self.accept()
        print("WebSocket connected - waiting for turnstile selection")

    async def disconnect(self, close_code):
        # Agar guruhga qo'shilgan bo'lsa, guruhdan chiqish
        if self.room_group_name:
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
        print(f"WebSocket disconnected: {close_code}")

    async def receive(self, text_data):
        # Clientdan turniket tanlash xabarini qabul qilish
        try:
            data = json.loads(text_data)
            action = data.get('action')

            if action == 'select_turnstile':
                turnstile_id = data.get('turnstile_id')
                await self.select_turnstile(turnstile_id)

        except Exception as e:
            print(f"Error processing message: {e}")

    async def select_turnstile(self, turnstile_id):
        # Agar avvalgi guruhda bo'lsa, chiqish
        if self.room_group_name:
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

        # Yangi turniket ID ni saqlash
        self.turnstile_id = turnstile_id
        self.room_group_name = f'turnstile_{turnstile_id}'

        # Yangi guruhga qo'shilish
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        # Clientga tasdiq yuborish
        await self.send(text_data=json.dumps({
            'type': 'turnstile_selected',
            'turnstile_id': turnstile_id,
            'message': f'Turniket #{turnstile_id} tanlandi'
        }))

        print(f"Client subscribed to turnstile: {turnstile_id}")

    # Group'dan xabar qabul qilish (faqat o'z turniketidan)
    async def student_access_event(self, event):
        # Ma'lumotlarni clientga yuborish
        await self.send(text_data=json.dumps({
            'type': 'student_access',
            'data': event['data']
        }))