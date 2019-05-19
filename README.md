# Projeto Integrador 2 
##### Alunos: Suyan Moriel e Yara Karoline


#### Sistema Supervisor: 
Este sistema fora dividido em 3 classes. 

* ComunicaComSA: 
    * Classe responsável por enviar dados para o Sistema Auditor 
    
    * Possui uma instância de Supervisor. 

    * Usa dois sockets, um dealer, para requisições individuais e outro subscribe para receber mensagens em broadcast. 

* Supervisor: 

    * Comunica-se diretamente com o S.R, através de um socket router. 

    * Processa as mensagens vindas do robô (a maioria do modo automático)

    * Envia mensagens para o robô. 

    * Possui uma instância de ComunicaComSA. 

* InterfaceDeJogo: 
    * Possui uma instância de Supervisor

    * Responsável por transmitir comandos do usuário para o SR. 

    * estes comandos são 
        * "w": ir para frente
        * "a": ir para esquerda
        * "s": ir para trás 
        * "d": ir para direita.
        * " ": (espaço), obter caça. 
    
    * Tais comandos, acima citados, estão disponiveis apenas no modo manual, no modo automático, eles estarão bloqueados. 
    
    * A responsábilidade por definir o modo de jogo(manual ou automático), é do árbitro.

* Mensagens Trocadas: 


    Todas as mensagens abaixo são **enviadas** pelo sistema auditor, e recebidas na classe ComunicaComSA


| cmd          | função                                      |                payload               | broadcast? |
|--------------|---------------------------------------------|:------------------------------------:|------------|
| START        | Informar ao SS o inicio da partida          | Lista de caças                       | SIM        |
| UPDATE_MAP   | Atualizar o mapa                            | Lista de posições ocupadas por robôs | SIM        |
| UPDATE_FLAGS | Atualizar lista de caças                    | Lista de caças                       | SIM        |
| MODE         | Define o modo de jogo. Manual ou Automático | True=Manual, False=Automático        | SIM        |
| STOP         | Termina a partida                           | Null                                 | SIM        |




Todas as mensagens abaixo são **enviadas** pelo sistema supervisor, na classe ComunicaComSA. 


| cmd      | função                              | payload                                           | resposta do S.A.                                                                              |
|----------|-------------------------------------|---------------------------------------------------|-----------------------------------------------------------------------------------------------|
| LOGIN    | Efetuar o login no Sistema Auditor  | {ID : id, IP : ip, INITIAL_POS : posição inicial} | STATUS(200 ou 400)                                                                            |
| MOVE_TO  | Informar a movimentação do robô     | (coordX, coordY)                                  | Null                                                                                          |
| GET_FLAG | Informar a obtenção de uma bandeira | (CoordX, CoordY)                                  | Se a bandeira for válida, o SA enviará a nova  lista de bandeiras, em broadcast(UPDATE_FLAGS) |


Todas as mensages abaixo são **recebidas** pelo sistema supervisor, na classe Supervisor.
Quem as envia é o S.R. 

| cmd           | função                                                              | payload          |
|---------------|---------------------------------------------------------------------|------------------|
| GET_FLAG      | Robo informa ao SS que achou bandeira (válido apenas no automático) | (CoordX, CoordY) |
| MOVE_TO       | Robô informa ao SS para onde quer ir  (válido apenas no automático) | (CoordX, CoordY) |
| CONNECT_TO_SS | Sistema do Robô efetua conexão com o Sistema Supervisor             | Null             |



Todas as mensagens abaixo são **enviadas** pelo sistema supervisor, na classe Supervisor. 

| cmd          | função                                                       | payload                         |
|--------------|--------------------------------------------------------------|---------------------------------|
| UPDATE_MAP   | envia lista de posições ocupadas por outros jogadores        | lista de posições ocupadas      |
| UPDATE_FLAGS | envia lista de bandeiras                                     | lista de bandeiras              |
| START        | Inicia robô                                                  | null                            |
| STOP         | Para robô                                                    | null                            |
| MOVE_TO      | Ordena robô a ir para determinada coordenada                 | (CoordX, CoordY)                |
| DIRECTION    | manda o robô ir para direção solicitada (uso do modo manual) | FRENTE, TRAS, DIREITA ESQUERDA. |
| MODE         | Informa ao SR o modo de jogo                                 | True=Manual, False=Automatico   |

