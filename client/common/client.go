package common

import (
	"bufio"
	"encoding/binary"
	"fmt"
	"io"
	"net"
	"os"
	"os/signal"
	"strings"
	"syscall"
	"time"

	"github.com/op/go-logging"
)

const CONFIRM_MSG_LEN = 3
const MAX_MSG_LEN = 4
const DONE_MESSAGE = "done:"
const SUCCESS_MSG = "succ"
const WAITING_MESSAGE = "wait"
const WINNER_SEPARATOR = ","
const EXIT = "exit"
var log = logging.MustGetLogger("log")

// ClientConfig Configuration used by the client
type ClientConfig struct {
	ID            string
	ServerAddress string
	LoopAmount    int
	LoopPeriod    time.Duration
	MaxBatchSize  int  
}

// Client Entity that encapsulates how
type Client struct {
	config ClientConfig
	conn   net.Conn
	isFinished bool
}

// NewClient Initializes a new client receiving the configuration
// as a parameter
func NewClient(config ClientConfig) *Client {
	client := &Client{
		config: config,
		isFinished: false,
	}

	InitializeSignalListener(client)
	return client
}

func InitializeSignalListener(client *Client) {
	signalChan := make(chan os.Signal, 1)
	signal.Notify(signalChan, os.Interrupt, syscall.SIGTERM)

	go func(client *Client) {
		signal := <-signalChan
		log.Info("action: signal_received | result: success | client_id: %v | signal: %v", client.config.ID, signal)
		err := client.Shutdown()
		if err != nil {
			log.Errorf("action: signal_shutdown | result: fail | client_id: %v | error: %v", client.config.ID, err)
		}
		log.Info("action: signal_shutdown | result: success | client_id: %v", client.config.ID)
	}(client)
}

// CreateClientSocket Initializes client socket. In case of
// failure, error is printed in stdout/stderr and exit 1
// is returned
func (c *Client) createClientSocket() error {
	conn, err := net.Dial("tcp", c.config.ServerAddress)
	if err != nil {
		log.Criticalf(
			"action: connect | result: fail | client_id: %v | error: %v",
			c.config.ID,
			err,
		)
		return err
	}
	c.conn = conn
	log.Info("action: connect | result: success | client_id: %v", c.config.ID)
	return nil
}

func (c* Client) SendMsgLen(msg_len int) error {
	msg_len_bytes := make([]byte, MAX_MSG_LEN)

	binary.LittleEndian.PutUint32(msg_len_bytes, uint32(msg_len))
	return c.SendAny(msg_len_bytes,true)
}

func (c *Client) SendMsg(msg []byte,wait_done bool) error {
	err := c.SendMsgLen(len(msg))
	if err != nil {
		// log.Errorf("action: send_message_len | result: fail | client_id: %v | error: %v", c.config.ID, err)
		return err
	}
	
	err = c.SendAny(msg,wait_done)
	if err != nil {
		log.Errorf("action: send_any_message | result: fail | client_id: %v | error: %v", c.config.ID, err)
		return err
	}
	return err

}

func (c *Client) SendAny(msg []byte, wait_done bool) error {
	var err error

	total_sent := 0
	msg_len := len(msg)

	for total_sent < msg_len {
		sent, err := c.conn.Write(msg[total_sent:])
		total_sent += sent
		if err != nil {
			// log.Errorf("action: send_any | result: fail | client_id: %v | error: %v", c.config.ID, err)
			return err
		}
	}
	if wait_done {
		err = c.ReceiveConfirmation()

		if err != nil {
			log.Errorf("action: receive_confirmation | result: fail | client_id: %v | error: %v", c.config.ID, err)
			return err
		}
	}

	return err
}

func (c *Client) ReceiveConfirmation() error {
	conf, err := c.SafeRecv(CONFIRM_MSG_LEN)
	if err != nil || len(conf) != CONFIRM_MSG_LEN {
		log.Errorf("action: receive_confirmation | result: fail | client_id: %v | error: %v", c.config.ID, err)
		return err
	}

	log.Info("action: receive_confirmation | result: success | client_id: %v %s", c.config.ID, conf)
	return err
}

func (c *Client) SafeRecv(length int) (res []byte, res_error error) {
	buf := make([]byte, length)
	total_read := 0
	result := make([]byte, length)

	var err error

	for total_read < length {
		read, err := c.conn.Read(buf)
		if err == io.EOF {
			// log.Info("action: safe_recv | result: success | client_id: %v, %s", c.config.ID, result)
			return result[:total_read], nil
		} else if err != nil {
			// log.Errorf("action: safe_recv | result: fail | client_id: %v | error: %v", c.config.ID, err)
			break
		} else if read == 0 {
			// log.Info("action: safe_recv | result: success | client_id: %v, read:", c.config.ID)
			return result, net.ErrClosed
		}
		copy(result[:len(buf)], buf)
		total_read += read
		buf = make([]byte, length)
	}
	// log.Infof("action: safe_recv | result: success | client_id: %v | read (string): %q", c.config.ID, string(result[:total_read]))
	return result, err
}

func (c *Client) Shutdown() error {

    if c.conn != nil {
        if err := c.conn.Close(); err != nil {
            log.Errorf("action: shutdown | result: fail | client_id: %v | error: %v",
                c.config.ID,
                err,
            )
            return err
        }
        log.Info("action: shutdown | result: success | client_id: %v | message: connection closed", c.config.ID)
    }

    c.isFinished = true
    log.Info("action: shutdown | result: success | client_id: %v | message: client finished", c.config.ID)

    return nil
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
		parts := strings.Split(line, ",")
		if len(parts) != 5 {
			continue 
		}
		bet := NewBet(agencyID, parts[0], parts[1], parts[2], parts[3], parts[4])
		bets = append(bets, bet)
	}

	return bets, nil
}


func (c *Client) ReceiveAndSendConfirmation() (res []byte, res_error error) {
	rcv_len, err := c.SafeRecv(MAX_MSG_LEN)

	c.SendAny([]byte(SUCCESS_MSG),false)

	msg_len := int(binary.LittleEndian.Uint32(rcv_len))
	if msg_len == 0 {
		return []byte{}, err
	}
	res, _ = c.SafeRecv(msg_len)

	return res, c.SendAny([]byte(SUCCESS_MSG),false)
}


// check 
func checkWinnersAnnouncementMsg(message []byte) bool {
	return message != nil && string(message) != WAITING_MESSAGE
}
func  AnnounceWinners(winners []string) {
	length := len(winners)
	if len(winners[0]) == 0 {
		length = 0
	}
	log.Infof("action: consulta_ganadores | result: success | cant_ganadores: %v", length)
}


func SendDoneMessage(client *Client) {
	message := fmt.Sprintf("done:%s", client.config.ID)

	for {
		client.createClientSocket()
		log.Info("action: sending_done | result: success | client_id: %v", client.config.ID)
		client.SendMsg([]byte(message),false)
		res, err := client.ReceiveAndSendConfirmation()
		if err != nil {
			break
		}
		if checkWinnersAnnouncementMsg(res) {
			winners := parseWinners(res)
			AnnounceWinners(winners)
			break
		}
		if client.conn != nil {
			client.conn.Close()
			client.conn = nil
		}
		time.Sleep(100 * time.Millisecond)
	}
	log.Info("action: exit | result: success | client_id: %v", client.config.ID)
	client.isFinished = true
	
}


func parseWinners(bytes []byte) []string {
	return strings.Split(string(bytes), WINNER_SEPARATOR)
}

