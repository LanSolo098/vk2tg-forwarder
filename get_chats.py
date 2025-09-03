import vk_api
from config import VK_TOKEN

vk_session = vk_api.VkApi(token= "vk1.a.Dwr8mjiOs7Kyuw4E_o8DAQSOYjCzBLH_wqjl6hhlxyHo1DNENK8nF-c2dYWAEiB9wR8BD1xVv_UxDm9sqUDrJgkMYPMryKpzamu9I5m-31m6Itecvix2hecWFjjftYU_JrkWSJ8wSgPInlilB117tG59TUjpX9ktbFXSNX-AtpykZ05poSELjQh19jHAwAdb4xt3KI2xNXtZ7oK1nwC3XA")
vk = vk_session.get_api()

conversations = vk.messages.getConversations(count=50)

print("Список бесед VK:")
for conv in conversations['items']:
    peer = conv['conversation']['peer']
    chat_settings = conv['conversation'].get('chat_settings')
    title = chat_settings.get('title') if chat_settings else None
    if title:
        print(f"{peer['id']} -> {title}")
