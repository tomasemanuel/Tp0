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

func (bet_agency *BetAgency) SendBet() {
	bet := bet_agency.bet
	err := bet_agency.client.StartClient(bet.serialize())

	if err != nil {
		log.Errorf("action: send_bet | result: fail | client_id: %v | error: %v", 
			bet_agency.client.config.ID, err)
		return
	}

	log.Infof("action: send_bet | result: success | client_id: %v", bet_agency.client.config.ID)
}

func (agency *BetAgency) Start() {
	agency.SendBet()
}