import asyncio
import aiohttp
import json

async def test_mastra_connection():
    """Mastraエージェントへの接続をテストする"""
    mastra_url = "http://localhost:4111/api/agents/telloAgent/generate"
    
    payload = {
        "messages": [{"role": "user", "content": "こんにちは"}],
        "threadId": "test",
        "resourceId": "user"
    }
    
    print(f"Testing connection to: {mastra_url}")
    print(f"Payload: {json.dumps(payload, ensure_ascii=False)}")
    
    try:
        timeout = aiohttp.ClientTimeout(total=30)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(
                mastra_url,
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as resp:
                print(f"Response status: {resp.status}")
                print(f"Response headers: {dict(resp.headers)}")
                
                if resp.status == 200:
                    response_data = await resp.json()
                    print(f"Response text: {response_data.get('text', 'No text field')}")
                    return True
                else:
                    error_text = await resp.text()
                    print(f"Error response: {error_text}")
                    return False
                    
    except Exception as e:
        print(f"Exception occurred: {e}")
        print(f"Exception type: {type(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_mastra_connection())
    print(f"Test result: {'SUCCESS' if result else 'FAILED'}") 