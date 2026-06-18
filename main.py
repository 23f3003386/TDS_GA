import os
import sys
import traceback
from io import StringIO
from typing import List
import re

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from google import genai
from google.genai import types

app = FastAPI(title="AI-Powered Code Interpreter Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],
)

class InterpreterRequest(BaseModel):
    code: str


class InterpreterResponse(BaseModel):
    error: List[int]
    result: str


class ErrorAnalysis(BaseModel):
    error_lines: List[int]

def execute_python_code(code: str) -> dict:
  local_vars = {}

  old_stdout = sys.stdout
  sys.stdout = StringIO()

  try:
    exec(code, {}, local_vars)
    output = sys.stdout.getvalue()
    return {"success": True, "output": output}
  except Exception as e:
    output = traceback.format_exc()
    return {"success": False, "output": output}
  finally:
    sys.stdout = old_stdout
  
def analyze_error_with_ai(code: str, traceback_str: str) -> List[int]:
    matches = re.findall(r"line (\d+)", traceback_str)
    if matches:
        exact_line = int(matches[-1])
        if exact_line <= len(code.splitlines()):
            return [exact_line]

    try:
        api_key = os.environ.get("GEMINI_API_KEY")
        client = genai.Client(api_key=api_key)
        

        numbered_code_lines = []
        for i, line in enumerate(code.splitlines(), start=1):
            numbered_code_lines.append(f"{i}: {line}")
        numbered_code = "\n".join(numbered_code_lines)

    prompt = f"""
        You are an expert Python code analyzer. Identify the exact line number(s) where the execution failed based on the provided traceback.
        
        CODE:
        {numbered_code}
        
        TRACEBACK:
        {traceback_str}
        
        Return the exact line number(s) as integers inside the "error_lines" array.
        """
    response = client.models.generate_content(
        model="gemini-2.0-flash-exp",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "error_lines": types.Schema(
                        type=types.Type.ARRAY,
                        items=types.Schema(type=types.Type.INTEGER),
                    )
                },
                required=["error_lines"],
            ),
        ),
    )
    result = ErrorAnalysis.model_validate_json(response.text)
    return result.error_lines

    except Exception:
        return []

@app.post("/code-interpreter", response_model=InterpreterResponse)
async def code_interpreter(payload: InterpreterRequest):

    execution_result = execute_python_code(payload.code)

    if execution_result["success"]:
        # Kod sorunsuz çalıştıysa AI'ı boşuna ÇAĞIRMIYORUZ (AI Only When Needed kuralı)
        return InterpreterResponse(error=[], result=execution_result["output"])

    try:
        error_lines = analyze_error_with_ai(
            code=payload.code, traceback_str=execution_result["output"]
        )
    except Exception:
        error_lines = []

    return InterpreterResponse(
        error=error_lines, result=execution_result["output"]
    )

