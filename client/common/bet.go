package common

import (
	"bufio"
	"fmt"
	"os"
	"strings"
)

type Bet struct {
	agency string
	first_name string
	last_name string
	document string
	birth_date string
	number string
}

func NewBet(agency string, first_name string, last_name string, document string, birth_date string, number string) *Bet {
	bet := &Bet{
		agency: agency,
		first_name: first_name,
		last_name: last_name,
		document: document,
		birth_date: birth_date,
		number: number,
	}
	return bet
}

func (b *Bet) Serialize() []byte {
	return []byte(fmt.Sprintf("%s|%s|%s|%s|%s|%s",
	b.agency, b.first_name, b.last_name, 
	b.document, b.birth_date, b.number))
}
func LoadBetsFromFile(path string, agencyID string) ([]*Bet, error) {
	file, err := os.Open(path)
	if err != nil {
		return nil, err
	}
	defer file.Close()

	var bets []*Bet
	scanner := bufio.NewScanner(file)
	for scanner.Scan() {
		line := scanner.Text()
		fields := strings.Split(line, ",")
		if len(fields) != 5 {
			continue
		}

		firstName := fields[0]
		lastName := fields[1]
		document := fields[2]
		birthDate := fields[3]
		number := fields[4]

		log.Infof("action: load_bet | result: success | agency_id: %v | first_name: %v | last_name: %v | document: %v | birth_date: %v | number: %v",)

		bet := NewBet(
			agencyID,
			firstName,
			lastName,
			document,
			birthDate,
			number,
		)
		bets = append(bets, bet)
	}

	if err := scanner.Err(); err != nil {
		return nil, err
	}

	return bets, nil
}
