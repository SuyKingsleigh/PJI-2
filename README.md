# Projeto Integrador 2 
#### Alunos: Suyan Moriel e Yara Karoline




<details><summary>Diagrama de caso de uso do S.S.:</summary>
<p>
 
 ### Diagrama de caso de uso do S.S.:

![diagramass](Caso de uso SS.jpeg)
</p>
</details>


<details><summary>Diagrama de caso de uso do S.R.:</summary>
<p>
 
 ### Diagrama de caso de uso do S.R.:
 
 ![diagramasr](sr-diagrama-caso-de-uso-2.png)

</p>
</details>


<details><summary>Diagrama de caso de uso do S.A.:</summary>
<p>

### Diagrama de caso de uso do S.A.:

 ![diagramasa](sa-diagrama-caso-de-uso.png)

</p>
</details>

<details><summary>Diagrama de clase(Mover):</summary>
<p>

### Diagrama de Classe (Mover):

![diagrama classe mover](diagrama-classe-mover.png)

</p>
</details>

## Casos de Uso:

<details><summary>Casos de uso do S.A.:</summary>
<p>
 
### Caso de uso S.A.:
##### Nome: Verifica tabuleiro
* Identificador: CSU.SA 01
* Sumário: Inicia a conexão entre S.A S.S
* Ator primário: S.S

###### Fluxo principal:

1. S.S envia ao S.A uma mensagem contendo o nome do robô, cor e senha. 

2. S.A válida os dados ou não.

###### Fluxo de exceções: 

1. Senha errada o Login errado:

2. Simplesmente envia uma mensagem ao S.S informando-o que não foi possível conectar devido a login e/ou senha errado(s)


##### Nome: Acessa histórico
* Identificador: CSU.SA 02
* Sumário: Envia histórico de partidas ao cliente. 
* Ator primário: S.A.
* Précondições: CSU.SA 01

###### Fluxo principal:	
1. S.S. solicita histórico de partidas ao S.A. 

2. S.A procura em seu banco de dados o histórico daquele cliente 
Caso tenha algo, envia o histórico, caso contrário informa que não há histórico.  

##### Nome: Inicia partida. 
* Identificador: CSU.SA 03
* Sumário: Inicia a partida, sorteando as caças e informando aos robôs suas posições
* Ator primário: S.A

###### Fluxo principal:	
1. Gera as posições das caças 
 
2. Informa a todos as posições das caças. 

3. Espera ack de todos para iniciar de fato.

###### Fluxo de exeção
* Não recebeu ack de todos os robôs: Envia posições novamente 


##### Nome: Valida caça. 
* Identificador: CSU.SA 04
* Sumário: Válida ou não a caça de um robô 
* Ator primário: SA.
* A partida ter começado (CSU.SA 03)

###### Fluxo principal:	

1. Recebe mensagem de caça obtida de algum determinado S.S

2. S.A verifica se realmente aquela caça é válida ou não

3. Caso seja validada, incrementa o placar e atualiza as caças, informado aos outros S.S.




##### Nome: Recebe informações dos robôs. 
* Identificador: CSU.SA 05
* Sumário: Recebe dados de movimentação dos robôs.
* Précondições: CSU.SA 03
* Ator primário: S.A.

###### Fluxo principal:	

1. S.S informa a posição de seu respectivo robô ao S.A 

2. S.A processa a informação 

3. S.A informa ao S.S a posição de outros robôs para evitar colisões. 

##### Nome: Declara vencedor
* Identificador: CSU.SA 06
* Sumário: Finaliza uma partida declarando o vencedor. 
* Ator primário: S.A. 
* Précondições: CSU.SA 03

###### Fluxo principal: 

1. Calcula a pontuação 

2. Informa a pontuação aos jogadores. 

3. Salva histórico de partida.


##### Nome: Pausa
* Identificador: CSU.SA 07
* Sumário: Pausa a partida caso o árbitro decida.
* Ator primário: S.A. 
* Précondições: CSU.SA 03
###### Fluxo principal: 

1. Envia mensagem de pause para os S.S.

2. Espera ACK

3. Uma vez todos os ACKs recebido, aguarda o recomeço da partida. 

4. Recomeça a partida de onde fora pausada. 

</p>
</details>

<details><summary>Casos de uso do S.S.:</summary>
<p>
 
### Caso de uso S.S.:
 ##### Nome: Start/Stop

Identificador: CSU SS 01;

Ator primário: S.A.;

Sumário: S.A. envia uma mensagem para S.S. pausar ou retornar com a movimentação dos robôs ;

Precondições: O jogo deve estar iniciado e rodando

###### Fluxo principal:

* 1.  O jogo deve ser iniciado

* 2.  S.A. deve enviar um comando para pausar/restartar para S.S.

* 3. S.S. encaminha o pedido  para o S.R.

* 4. S.R. executa o pedido.

##### Nome: Recebe informações

Identificador: CSU SS 02;

Sumário: Com a conexão estabelecida, o SR tem condições de receber os dados do jogo do SS: coordenadas inicial e das caças, modo de operação, etc.;

Ator primário: Sistema Supervisório;

Precondições:

Robô já ter sido cadastrado;

O robô já ter se autenticado;

###### Fluxo principal:

* 1. SS envia os dados para o robô para início do jogo;

* 2. SR processa os dados, define sua posição inicial e mapeia as caças do jogo;


##### Nome: Comunicação entre SR e SS

Identificador: CSU SS 03;

Sumário: S.R. envia e recebes dados de S.S.

Ator primário: Sistema Supervisório;

###### Fluxo principal:

* S.S envia informações ao S.R, como posição das caças.

* S.R envia informações ao S.S, como sua própria posição. 


##### Nome: Movimenta-se automaticamente

Identificador: CSU SS 04;

Sumário: Uma vez definido como operação automática, o algoritmo de busca das caças, anteriormente declaradas através de coordenadas, é executado, tendo como fonte de informação os sensores do robô - luminosidade (cor) e ultrassônico(distância), além de contar com os motores para deslocamento.

Atores primários: Sensores, Motores.

Precondições:

Ter recebido os dados com sucesso.

Posição inicial correta (0,0 ou 20,20).

###### Fluxo principal:

* 1. Ao se deparar com uma caça, enviar informação ao SS.

* 2. Fluxo de exceção:

###### Fluxo de exceção: 

* 1. Obstáculo próximo (mudar trajetória).

* 2. Se pausar, o robô fica parado esperando o retorno do jogo.

* 3. Se terminar o jogo o robô deverá voltar ao ponto inicial.

* 4. Se recebe falha de validação da caça.


##### Nome: Movimenta-se manualmente

Identificador: CSU05;

Sumário: O usuário fica responsável pelo controle do robô e envio das informações de caças.;

Ator primário:Jogador.

Precondições:

Posição inicial correta (0,0 ou 20,20);

###### Fluxo principal:

Usuário controla livremente o robô através de uma interface gráfica simplista. 



##### Nome: Obtém caça

Identificador: CSU SS 06;

Sumário: S.R. informa à S.S. as caças conquistadas;

Ator primário: Sistema Supervisório, Motores;


Precondições: 

* Partida ter começado

###### Fluxo principal:

1. S.S. envia os dados ao SA, para atualização de caça conquistada.

2. Caso a caça seja validada, o placar é atualizado e o robô parte em busca da próxima.



##### Nome: Verifica tabuleiro

Identificador: CSU SS 07;

Sumário: Neste modo a SS envia as informações de caça ao robô

Ator primário: Sistema Supervisório

Precondições: 

* Partida ter começado. 

###### Fluxo principal:

1. S.S. processa os dados e mapeia novas caças do jogo.
 
 <details><summary>Diagrama de caso de uso do S.R.:</summary>
<p>
 </p>
 </details>


 
### Caso de uso S.R.:

</p>
 </details>




 <details><summary>Requisitos funcionais.:</summary>
<p>
 
## Requisitos funcionais:
RF01 O sistema deve permitir criação e gerência de cadastro de um robô.

RF02 O sistema de deve manter um histórico das partidas realizadas.

RF03 O sistema deve ser capaz de fazer a autenticação dos robôs cadastrados.

RF04 os robôs devem ser capazes de operar nos modos manual e autônomo.

RF05 O sistema deve validar e contabilizar as caças já encontradas pelo robô.

RF06 O sistema deve dar início a partida, sortear os locais das caças e informá-los aos robôs.

RF07 O sistema deve prover uma interface de monitoramento para o robô em modo autônomo.

RF08 O sistema deve prover uma interface de controle e monitoramento para os robôs em modo manual.

RF09 O sistema deve permitir que, quando em modo autônomo, o robô execute os movimentos programados a partir do algoritmo implementado.

RF010 O sistema deve permitir pausa e reset da partida.

RF011 O sistema deve permitir que os resultados do jogo sejam vistos pelos espectadores em tempo real.

RF012 O sistema não deve permitir que os robôs se choquem.

RF013 O sistema deve declarar um vencedor assim que todas as caças forem encontradas.

RF014 O sistema pode ter N competidores *

RF015 O sistema deve projetar informações no tabuleiro (Caças ativas, Caças encontradas, e placar) 

 </p>
 </details>
