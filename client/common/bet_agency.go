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
	log.Info("action: load_bet | result: success | agency_id: %v | first_name: %v | last_name: %v | document: %v | birth_date: %v | number: %v",
		betAgency.client.config.ID, betAgency.bet.first_name, betAgency.bet.last_name, betAgency.bet.document, betAgency.bet.birth_date, betAgency.bet.number)
}

func SendBetsInBatches(client *Client, bets []*Bet, maxBatchSize int) {
	client.createClientSocket()
	// log.Info("action: create_socket | result: success | client_id: %v and max batch size %d", client.config.ID, maxBatchSize)
	for i := 0; i < len(bets); i += maxBatchSize {
		end := i + maxBatchSize
		if end > len(bets) {
			end = len(bets)
		}
		batch := bets[i:end]
	
		serialized := SerializeBatch(batch)
		// log.Info("action: serialize_batch | result: success | client_id: %v | batch_size: %d", client.config.ID, len(batch))
		var err = client.SendMsg(serialized,true)
		if err != nil {
			// log.Errorf("action: send_message | result: fail | client_id: %v | error: %v")
			client.Shutdown()
			return
		}
		// log.Info("action: send_message | result: success | client_id: %v", client.config.ID)
	}

	// client.Shutdown() // This line is commented out to avoid closing the connection before the server has finished processing the messages
}

