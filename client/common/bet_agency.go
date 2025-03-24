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

func SendBetsInBatches(client *Client, bets []*Bet, maxBatchSize int) {
	client.createClientSocket()
	for i := 0; i < len(bets); i += maxBatchSize {
		end := i + maxBatchSize
		if end > len(bets) {
			end = len(bets)
		}
		batch := bets[i:end]
		serialized := SerializeBatch(batch)
		var err = client.SendMsg(serialized)
		if err != nil {
			log.Errorf("action: send_message | result: fail | client_id: %v | error: %v")
			client.Shutdown()
			return
		}
		log.Info("action: send_message | result: success | client_id: %v", client.config.ID)
	}
}

