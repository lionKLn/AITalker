import requests


class Kimi:
    def __init__(self, api_key, prefix_prompt='你是一位面试官\n\n'):
        self.api_key = api_key
        self.prefix_prompt = ""
        self.history = []

        self.api_url = "https://api.moonshot.cn/v1/chat/completions"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

    def generate(self, question, system_prompt=""):
        return self.predict_api(question, system_prompt)

    def predict_api(self, question, system_prompt=""):
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        for q, a in self.history:
            messages.append({"role": "user", "content": q})
            messages.append({"role": "assistant", "content": a})

        full_prompt = self.prefix_prompt + question
        messages.append({"role": "user", "content": full_prompt})

        payload = {
            "model": "moonshot-v1-128k",  # 或你实际使用的模型名
            "messages": messages,
            "temperature": 0.7,
            "top_p": 0.95,
            "max_tokens": 2048,
        }

        try:
            response = requests.post(self.api_url, headers=self.headers, json=payload)
            response.raise_for_status()
            result = response.json()
            reply = result["choices"][0]["message"]["content"]
            return reply
        except Exception as e:
            print(f"Kimi API 调用失败: {e}")
            return "对不起，Kimi 接口出错了，请稍后再试。"

    def chat(self, system_prompt, message, history):
        response = self.generate(message, system_prompt)
        history.append((message, response))
        return response, history

    def clear_history(self):
        self.history = []


def test():
    # 替换成你的实际 API KEY
    api_key = "sk-pko435BmmBJLN0mTyl5b2khWEea8b1us2gQFrqQDulhUPzUI"
    llm = Kimi(api_key=api_key)
    answer = llm.generate("如何应对压力？")
    print(answer)


if __name__ == '__main__':
    test()
