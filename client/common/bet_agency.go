package common

type BetAgency struct {
	bet *Bet
	client *Client
}

func NewBetAgency(client_config ClientConfig, name string, last_name string, document string,
	birthdate string, number string) *BetAgency {
		client := NewClient(client_config)

		bet := NewBet(client_config.ID, name, last_name, document, birthdate, number)
		bet_agency := &BetAgency{
			bet: bet,
			client: client,
		}

	return bet_agency
}

func PrintBetAgency(betAgency *BetAgency) {
	log.Infof("action: load_bet | result: success | agency_id: %v | first_name: %v | last_name: %v | document: %v | birth_date: %v | number: %v",
		betAgency.client.config.ID, betAgency.bet.first_name, betAgency.bet.last_name, betAgency.bet.document, betAgency.bet.birth_date, betAgency.bet.number)
}

func (bet_agency *BetAgency) SendBet() {
	bet := bet_agency.bet

	log.Infof("action: apuesta_enviada | result: success | dni: %s", bet.document)

	err := bet_agency.client.StartClient(bet.Serialize())
	if err != nil {
		log.Errorf("action: send_bet | result: fail | client_id: %v | error: %v", 
			bet_agency.client.config.ID, err)
		return
	}

	log.Infof("action: send_bet | result: success | client_id: %v", bet_agency.client.config.ID)
}

func SendBetsInBatches(client *Client, bets []*Bet, maxBatchSize int) {
	for i := 0; i < len(bets); i += maxBatchSize {
		end := i + maxBatchSize
		if end > len(bets) {
			end = len(bets)
		}
		batch := bets[i:end]
		serialized := SerializeBatch(batch)

		err := client.StartClient(serialized)
		if err != nil {
			log.Errorf("action: send_batch | result: fail | error: %v", err)
		} else {
			log.Infof("action: send_batch | result: success | size: %d", len(batch))
		}
	}
}



func (agency *BetAgency) Start() {
	agency.SendBet()
}