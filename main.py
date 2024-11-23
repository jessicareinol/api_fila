from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

app = FastAPI()

#p/ criar os clientes na fila
class Cliente(BaseModel):
    nome: str = Field(max_length=20) #deixa até 20 caracteres
    tipo: str  #pra validar N ou P na fila

#armazenamento
fila_normal = []
fila_prioritaria = []
contador_id = 0  #ids únicos

#calcula posição na fila
def atualizar_posicao():
    for posicao, cliente in enumerate(fila_prioritaria + fila_normal, start=1):
        cliente['posicao'] = posicao

@app.get("/fila")
async def obter_fila():
    if not fila_prioritaria and not fila_normal:
        return []
    return fila_prioritaria + fila_normal

@app.get("/fila/{id}")
async def obter_cliente(id: int):
    fila = fila_prioritaria + fila_normal
    for cliente in fila:
        if cliente["id"] == id:
            return cliente
    raise HTTPException(status_code=404, detail="Cliente não encontrado.")

@app.post("/fila")
async def adicionar_cliente(cliente: Cliente):
    global contador_id
    #p/ verificar o tipo de atendimento
    if cliente.tipo not in ["N", "P"]:
        raise HTTPException(
            status_code=400, 
            detail="O tipo de atendimento deve ser 'N' (Normal) ou 'P' (Prioritário)."
        )

    contador_id += 1
    novo_cliente = {
        "id": contador_id,
        "nome": cliente.nome,
        "tipo": cliente.tipo,
        "data_chegada": datetime.now(),
        "atendido": False,
        "posicao": 0  #vai atualizando a posiçã na fila
    }
    if cliente.tipo == "P":
        fila_prioritaria.append(novo_cliente)
    else:
        fila_normal.append(novo_cliente)
    atualizar_posicao()
    return novo_cliente

@app.put("/fila")
async def atualizar_fila():
    fila = fila_prioritaria + fila_normal
    if not fila:
        raise HTTPException(status_code=400, detail="Não há clientes na fila.")
    
    for cliente in fila:
        if cliente["posicao"] == 1:
            cliente["posicao"] = 0
            cliente["atendido"] = True
        else:
            cliente["posicao"] -= 1

    return fila

@app.delete("/fila/{id}")
async def remover_cliente(id: int):
    global fila_prioritaria, fila_normal
    fila = fila_prioritaria + fila_normal
    cliente_removido = None

    for lista in (fila_prioritaria, fila_normal):
        for cliente in lista:
            if cliente["id"] == id:
                cliente_removido = cliente
                lista.remove(cliente)
                break
        if cliente_removido:
            break

    if not cliente_removido:
        raise HTTPException(status_code=404, detail="Cliente não encontrado.")
    
    atualizar_posicao()
    return {"message": "Cliente removido com sucesso."}